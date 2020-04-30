import os
import json
import docker
import logging
import functools
import threading

from subprocess import check_output
from django.conf import settings
from requests.auth import HTTPBasicAuth
from substrapp.utils import get_owner, get_remote_file_content, get_and_put_remote_file_content, NodeError

from kubernetes import client, config

CELERYWORKER_IMAGE = os.environ.get('CELERYWORKER_IMAGE', 'substrafoundation/celeryworker:latest')
CELERY_WORKER_CONCURRENCY = int(getattr(settings, 'CELERY_WORKER_CONCURRENCY'))
DOCKER_LABEL = 'substra_task'

logger = logging.getLogger(__name__)

import time


def timeit(function):
    def timed(*args, **kw):
        ts = time.time()
        result = function(*args, **kw)
        elaps = (time.time() - ts) * 1000
        logger.info(f'{function.__name__} - elaps={elaps:.2f}ms')
        return result
    return timed


def authenticate_worker(node_id):
    from node.models import OutgoingNode

    owner = get_owner()

    try:
        outgoing = OutgoingNode.objects.get(node_id=node_id)
    except OutgoingNode.DoesNotExist:
        raise NodeError(f'Unauthorized to call node_id: {node_id}')

    auth = HTTPBasicAuth(owner, outgoing.secret)

    return auth


def get_asset_content(url, node_id, content_hash, salt=None):
    return get_remote_file_content(url, authenticate_worker(node_id), content_hash, salt=salt)


def get_and_put_asset_content(url, node_id, content_hash, content_dst_path, salt=None):
    return get_and_put_remote_file_content(url, authenticate_worker(node_id), content_hash,
                                           content_dst_path=content_dst_path, salt=salt)


def local_memory_limit():
    # Max memory in mb
    try:
        return int(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024. ** 2)) // CELERY_WORKER_CONCURRENCY
    except ValueError:
        # fixes macOS issue https://github.com/SubstraFoundation/substra-backend/issues/262
        return int(check_output(['sysctl', '-n', 'hw.memsize']).strip()) // CELERY_WORKER_CONCURRENCY


def docker_memory_limit():
    docker_client = docker.from_env()
    # Get memory limit from docker container through the API
    # Because the docker execution may be remote

    cmd = f'python3 -u -c "import os; print(int(os.sysconf("SC_PAGE_SIZE") '\
          f'* os.sysconf("SC_PHYS_PAGES") / (1024. ** 2)) // {CELERY_WORKER_CONCURRENCY}), end=\'\')"'

    task_args = {
        'image': CELERYWORKER_IMAGE,
        'command': cmd,
        'detach': False,
        'stdout': True,
        'stderr': True,
        'auto_remove': False,
        'remove': True,
        'network_disabled': True,
        'network_mode': 'none',
        'privileged': False,
        'cap_drop': ['ALL'],
    }

    memory_limit_bytes = docker_client.containers.run(**task_args)

    return int(memory_limit_bytes)


@timeit
def get_memory_limit():

    try:
        memory_limit = docker_memory_limit()
    except (docker.errors.ContainerError, docker.errors.ImageNotFound,
            docker.errors.APIError, ValueError):
        logger.info('[Warning] Cannot get memory limit from remote, get it from local.')
        memory_limit = local_memory_limit()

    return memory_limit


@timeit
def get_cpu_count(client):
    # Get CPU count from docker container through the API
    # Because the docker execution may be remote

    task_args = {
        'image': CELERYWORKER_IMAGE,
        'command': 'python3 -u -c "import os; print(os.cpu_count())"',
        'detach': False,
        'stdout': True,
        'stderr': True,
        'auto_remove': False,
        'remove': True,
        'network_disabled': True,
        'network_mode': 'none',
        'privileged': False,
        'cap_drop': ['ALL'],
    }

    cpu_count = os.cpu_count()

    try:
        cpu_count_bytes = client.containers.run(**task_args).strip()
    except (docker.errors.ContainerError, docker.errors.ImageNotFound, docker.errors.APIError):
        logger.info('[Warning] Cannot get cpu count from remote')
    else:
        if cpu_count_bytes:
            cpu_count = int(cpu_count_bytes)

    return cpu_count


@timeit
def get_cpu_sets(client, concurrency):
    cpu_count = get_cpu_count(client)
    cpu_step = max(1, cpu_count // concurrency)
    cpu_sets = []

    for cpu_start in range(0, cpu_count, cpu_step):
        cpu_set = f'{cpu_start}-{min(cpu_start + cpu_step - 1, cpu_count - 1)}'
        cpu_sets.append(cpu_set)
        if len(cpu_sets) == concurrency:
            break

    return cpu_sets


def get_gpu_list(client):
    # Get GPU list from docker container through the API
    # Because the docker execution may be remote
    cmd = 'python3 -u -c "import GPUtil as gputil;import json;'\
          'print(json.dumps([str(gpu.id) for gpu in gputil.getGPUs()]), end=\'\')"'

    task_args = {
        'image': CELERYWORKER_IMAGE,
        'command': cmd,
        'detach': False,
        'stdout': True,
        'stderr': True,
        'auto_remove': False,
        'remove': True,
        'network_disabled': True,
        'network_mode': 'none',
        'privileged': False,
        'cap_drop': ['ALL'],
        'environment': {'CUDA_DEVICE_ORDER': 'PCI_BUS_ID',
                        'NVIDIA_VISIBLE_DEVICES': 'all'},
        'runtime': 'nvidia'
    }

    gpu_list = []

    try:
        gpu_list_bytes = client.containers.run(**task_args)
    except (docker.errors.ContainerError, docker.errors.ImageNotFound, docker.errors.APIError):
        logger.info('[Warning] Cannot get nvidia gpu list from remote')
    else:
        gpu_list = json.loads(gpu_list_bytes)

    return gpu_list


def get_gpu_sets(client, concurrency):

    gpu_list = get_gpu_list(client)

    if gpu_list:
        gpu_count = len(gpu_list)
        gpu_step = max(1, gpu_count // concurrency)
        gpu_sets = []

        for igpu_start in range(0, gpu_count, gpu_step):
            gpu_sets.append(','.join(gpu_list[igpu_start: igpu_start + gpu_step]))
    else:
        gpu_sets = None

    return gpu_sets


def expand_cpu_set(cpu_set):
    cpu_set_start, cpu_set_stop = map(int, cpu_set.split('-'))
    return set(range(cpu_set_start, cpu_set_stop + 1))


def reduce_cpu_set(expanded_cpu_set):
    return f'{min(expanded_cpu_set)}-{max(expanded_cpu_set)}'


def expand_gpu_set(gpu_set):
    return set(gpu_set.split(','))


def reduce_gpu_set(expanded_gpu_set):
    return ','.join(sorted(expanded_gpu_set))


def filter_resources_sets(used_resources_sets, resources_sets, expand_resources_set, reduce_resources_set):
    """ Filter resources_set used with resources_sets defined.
        It will block a resources_set from resources_sets if an used_resources_set in a subset of a resources_set"""

    resources_expand = [expand_resources_set(resources_set) for resources_set in resources_sets]
    used_resources_expand = [expand_resources_set(used_resources_set) for used_resources_set in used_resources_sets]

    real_used_resources_sets = []

    for resources_set in resources_expand:
        for used_resources_set in used_resources_expand:
            if resources_set.intersection(used_resources_set):
                real_used_resources_sets.append(reduce_resources_set(resources_set))
                break

    return list(set(resources_sets).difference(set(real_used_resources_sets)))


def filter_cpu_sets(used_cpu_sets, cpu_sets):
    return filter_resources_sets(used_cpu_sets, cpu_sets, expand_cpu_set, reduce_cpu_set)


def filter_gpu_sets(used_gpu_sets, gpu_sets):
    return filter_resources_sets(used_gpu_sets, gpu_sets, expand_gpu_set, reduce_gpu_set)


def get_cpu_gpu_sets():

    docker_client = docker.from_env()

    cpu_sets = get_cpu_sets(docker_client, CELERY_WORKER_CONCURRENCY)
    gpu_sets = get_gpu_sets(docker_client, CELERY_WORKER_CONCURRENCY)  # Can be None if no gpu

    cpu_set = None
    gpu_set = None

    while cpu_set is None:

        # Get ressources used
        filters = {'status': 'running',
                   'label': [DOCKER_LABEL]}

        try:
            containers = [container.attrs
                          for container in docker_client.containers.list(filters=filters)]
        except docker.errors.APIError as e:
            logger.error(e, exc_info=True)
            continue

        # CPU
        used_cpu_sets = [container['HostConfig']['CpusetCpus']
                         for container in containers
                         if container['HostConfig']['CpusetCpus']]

        cpu_sets_available = filter_cpu_sets(used_cpu_sets, cpu_sets)

        if cpu_sets_available:
            cpu_set = cpu_sets_available.pop()

        # GPU
        if gpu_sets is not None:
            env_containers = [container['Config']['Env']
                              for container in containers]

            used_gpu_sets = []

            for env_list in env_containers:
                nvidia_env_var = [s.split('=')[1]
                                  for s in env_list if "NVIDIA_VISIBLE_DEVICES" in s]

                used_gpu_sets.extend(nvidia_env_var)

            gpu_sets_available = filter_gpu_sets(used_gpu_sets, gpu_sets)

            if gpu_sets_available:
                gpu_set = gpu_sets_available.pop()

    return cpu_set, gpu_set


def container_format_log(container_name, container_logs):
    logs = [f'[{container_name}] {log}' for log in container_logs.decode().split('\n')]
    for log in logs:
        logger.info(log)


def list_files(startpath):
    if not settings.TASK['LIST_WORKSPACE']:
        return
    if os.path.exists(startpath):

        for root, dirs, files in os.walk(startpath, followlinks=True):
            level = root.replace(startpath, '').count(os.sep)
            indent = ' ' * 4 * (level)
            logger.info(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                logger.info(f'{subindent}{f}')

        logger.info('\n')
    else:
        logger.info(f'{startpath} does not exist.')


def compute_docker(client, dockerfile_path, image_name, container_name, volumes, command,
                   environment, remove_image=True, remove_container=True, capture_logs=True):

    dockerfile_fullpath = os.path.join(dockerfile_path, 'Dockerfile')
    if not os.path.exists(dockerfile_fullpath):
        raise Exception(f'Dockerfile does not exist : {dockerfile_fullpath}')

    build_image = True

    # Check if image already exist
    try:
        ts = time.time()
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        logger.info(f'ImageNotFound: {image_name}. Building it')
    else:
        logger.info(f'ImageFound: {image_name}. Use it')
        build_image = False
    finally:
        elaps = (time.time() - ts) * 1000
        logger.info(f'client.images.get - elaps={elaps:.2f}ms')

    if build_image:
        try:
            ts = time.time()
            client.images.build(path=dockerfile_path,
                                tag=image_name,
                                rm=remove_image)
        except docker.errors.BuildError as e:
            # catch build errors and print them for easier debugging of failed build
            lines = [line['stream'].strip() for line in e.build_log if 'stream' in line]
            lines = [l for l in lines if l]
            error = '\n'.join(lines)
            logger.error(f'BuildError: {error}')
            raise
        else:
            logger.info(f'BuildSuccess - {image_name} - keep cache : {remove_image}')
            elaps = (time.time() - ts) * 1000
            logger.info(f'client.images.build - elaps={elaps:.2f}ms')

    # Limit ressources
    memory_limit_mb = f'{get_memory_limit()}M'
    cpu_set, gpu_set = get_cpu_gpu_sets()    # blocking call

    logger.info(f'Launch container {container_name} with {cpu_set} CPU - {gpu_set} GPU - {memory_limit_mb}.')

    task_args = {
        'image': image_name,
        'name': container_name,
        'cpuset_cpus': cpu_set,
        'mem_limit': memory_limit_mb,
        'command': command,
        'volumes': volumes,
        'shm_size': '8G',
        'labels': [DOCKER_LABEL],
        'detach': False,
        'stdout': capture_logs,
        'stderr': capture_logs,
        'auto_remove': False,
        'remove': False,
        'network_disabled': True,
        'network_mode': 'none',
        'privileged': False,
        'cap_drop': ['ALL'],
        'environment': environment
    }

    if gpu_set is not None:
        task_args['environment'].update({'NVIDIA_VISIBLE_DEVICES': gpu_set})
        task_args['runtime'] = 'nvidia'

    try:
        ts = time.time()
        client.containers.run(**task_args)
    finally:
        # we need to remove the containers to be able to remove the local
        # volume in case of compute plan
        container = client.containers.get(container_name)
        if capture_logs:
            container_format_log(
                container_name,
                container.logs()
            )
        container.remove()

        # Remove images
        if remove_image:
            client.images.remove(image_name, force=True)

        elaps = (time.time() - ts) * 1000
        logger.info(f'client.images.run - elaps={elaps:.2f}ms')


def get_k8s_client():
    config.load_incluster_config()
    return client.CoreV1Api()


def do_not_raise(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logging.exception(e)
    return wrapper


class ExceptionThread(threading.Thread):

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self._exception = e
            raise e
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs

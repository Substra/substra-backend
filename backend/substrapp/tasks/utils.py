import os
import json
import docker
import logging
import functools
import threading

from subprocess import check_output
from django.conf import settings
from requests.auth import HTTPBasicAuth
from substrapp.utils import get_owner, get_remote_file_content, get_and_put_remote_file_content, NodeError, timeit

from substrapp.tasks.docker_backend import (
    docker_memory_limit, docker_cpu_count, docker_cpu_used, docker_gpu_list, docker_gpu_used, docker_get_image,
    docker_build_image, docker_remove_local_volume, docker_get_or_create_local_volume, docker_remove_image,
    docker_compute)
from substrapp.tasks.k8s_backend import (
    k8s_memory_limit, k8s_cpu_count, k8s_cpu_used, k8s_gpu_list, k8s_gpu_used, k8s_get_image, k8s_build_image,
    k8s_remove_local_volume, k8s_get_or_create_local_volume, k8s_remove_image, k8s_compute, ImageNotFound,
    BuildError)


CELERYWORKER_IMAGE = os.environ.get('CELERYWORKER_IMAGE', 'substrafoundation/celeryworker:latest')
CELERY_WORKER_CONCURRENCY = int(getattr(settings, 'CELERY_WORKER_CONCURRENCY'))
TASK_LABEL = 'substra_task'
COMPUTE_BACKEND = settings.TASK['COMPUTE_BACKEND']

logger = logging.getLogger(__name__)

import time

BACKEND = {
    'docker': {
        'get_memory': docker_memory_limit,
        'get_cpu': docker_cpu_count,
        'get_cpu_used': docker_cpu_used,
        'get_gpu': docker_gpu_list,
        'get_gpu_used': docker_gpu_used,
        'get_image': docker_get_image,
        'build_image': docker_build_image,
        'local_volume': docker_get_or_create_local_volume,
        'rm_local_volume': docker_remove_local_volume,
        'remove_image': docker_remove_image,
        'compute': docker_compute,
    },

    'k8s': {
        'get_memory': k8s_memory_limit,
        'get_cpu': k8s_cpu_count,
        'get_cpu_used': k8s_cpu_used,
        'get_gpu': k8s_gpu_list,
        'get_gpu_used': k8s_gpu_used,
        'get_image': k8s_get_image,
        'build_image': k8s_build_image,
        'local_volume': k8s_get_or_create_local_volume,
        'rm_local_volume': k8s_remove_local_volume,
        'remove_image': k8s_remove_image,
        'compute': k8s_compute,
    },

}


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


@timeit
def get_memory_limit(concurrency=None):

    if concurrency is None:
        concurrency = CELERY_WORKER_CONCURRENCY

    try:
        memory_limit = BACKEND[COMPUTE_BACKEND]['get_memory'](concurrency, CELERYWORKER_IMAGE)
    except (docker.errors.ContainerError, docker.errors.ImageNotFound,
            docker.errors.APIError, ValueError):
        logger.info('[Warning] Cannot get memory limit from remote, get it from local.')
        memory_limit = local_memory_limit()

    return memory_limit


@timeit
def get_cpu_count():

    cpu_count = os.cpu_count()

    try:
        cpu_count_bytes = BACKEND[COMPUTE_BACKEND]['get_cpu'](CELERYWORKER_IMAGE)
    except (docker.errors.ContainerError, docker.errors.ImageNotFound, docker.errors.APIError):
        logger.info('[Warning] Cannot get cpu count from remote')
    else:
        if cpu_count_bytes:
            cpu_count = int(cpu_count_bytes)

    return cpu_count


@timeit
def get_cpu_sets(concurrency=None):

    if concurrency is None:
        concurrency = CELERY_WORKER_CONCURRENCY

    cpu_count = get_cpu_count()
    cpu_step = max(1, cpu_count // concurrency)
    cpu_sets = []

    for cpu_start in range(0, cpu_count, cpu_step):
        cpu_set = f'{cpu_start}-{min(cpu_start + cpu_step - 1, cpu_count - 1)}'
        cpu_sets.append(cpu_set)
        if len(cpu_sets) == concurrency:
            break

    return cpu_sets


def get_gpu_list():

    gpu_list = []

    try:
        gpu_list_bytes = BACKEND[COMPUTE_BACKEND]['get_gpu'](CELERYWORKER_IMAGE)
    except (docker.errors.ContainerError, docker.errors.ImageNotFound, docker.errors.APIError):
        logger.info('[Warning] Cannot get nvidia gpu list from remote')
    else:
        if gpu_list_bytes:
            try:
                gpu_list = json.loads(gpu_list_bytes)
            except json.JSONDecodeError:
                logger.info(f'[Warning] Cannot get nvidia gpu list from remote (JSONDecodeError on: "{gpu_list_bytes}"')

    return gpu_list


def get_gpu_sets(concurrency=None):

    if concurrency is None:
        concurrency = CELERY_WORKER_CONCURRENCY

    gpu_list = get_gpu_list()

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

    cpu_sets = get_cpu_sets()
    gpu_sets = get_gpu_sets()  # Can be None if no gpu

    cpu_set = None
    gpu_set = None

    while cpu_set is None:

        # Get ressources used
        try:
            used_cpu_sets = BACKEND[COMPUTE_BACKEND]['get_cpu_used'](TASK_LABEL)
        except docker.errors.APIError as e:
            logger.error(e, exc_info=True)
            continue

        cpu_sets_available = filter_cpu_sets(used_cpu_sets, cpu_sets)

        if cpu_sets_available:
            cpu_set = cpu_sets_available.pop()

        # GPU
        if gpu_sets is not None:
            try:
                used_gpu_sets = BACKEND[COMPUTE_BACKEND]['get_gpu_used'](TASK_LABEL)
            except docker.errors.APIError as e:
                logger.error(e, exc_info=True)
            else:
                gpu_sets_available = filter_gpu_sets(used_gpu_sets, gpu_sets)
                if gpu_sets_available:
                    gpu_set = gpu_sets_available.pop()

    return cpu_set, gpu_set


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


def get_or_create_local_volume(volume_id):
    return BACKEND[COMPUTE_BACKEND]['local_volume'](volume_id)


def remove_local_volume(volume_id):
    return BACKEND[COMPUTE_BACKEND]['rm_local_volume'](volume_id)


def remove_image(image_name):
    return BACKEND[COMPUTE_BACKEND]['remove_image'](image_name)


def raise_if_no_dockerfile(dockerfile_path):
    dockerfile_fullpath = os.path.join(dockerfile_path, 'Dockerfile')
    if not os.path.exists(dockerfile_fullpath):
        raise Exception(f'Dockerfile does not exist : {dockerfile_fullpath}')


def container_format_log(container_name, container_logs):
    logs = [f'[{container_name}] {log}' for log in container_logs.decode().split('\n')]
    for log in logs:
        logger.info(log)


@timeit
def compute_job(subtuple_key, dockerfile_path, image_name, job_name, volumes, command,
                environment, remove_image=True, remove_container=True, capture_logs=True):

    raise_if_no_dockerfile(dockerfile_path)

    build_image = True

    # Check if image already exist
    try:
        ts = time.time()
        BACKEND[COMPUTE_BACKEND]['get_image'](image_name)
    except (docker.errors.ImageNotFound, ImageNotFound):
        logger.info(f'ImageNotFound: {image_name}. Building it')
    else:
        logger.info(f'ImageFound: {image_name}. Use it')
        build_image = False
    finally:
        elaps = (time.time() - ts) * 1000
        logger.info(f'{COMPUTE_BACKEND} get image  - elaps={elaps:.2f}ms')

    if build_image:
        try:
            ts = time.time()
            BACKEND[COMPUTE_BACKEND]['build_image'](
                path=dockerfile_path,
                tag=image_name,
                rm=remove_image)
        except (docker.errors.BuildError, BuildError) as e:
            if isinstance(e, docker.errors.BuildError):
                # catch build errors and print them for easier debugging of failed build
                lines = [line['stream'].strip() for line in e.build_log if 'stream' in line]
                lines = [line for line in lines if line]
                error = '\n'.join(lines)
            else:
                error = '\n' + str(e)
            logger.error(f'BuildError: {error}')
            raise
        else:
            logger.info(f'BuildSuccess - {image_name} - keep cache : {remove_image}')
            elaps = (time.time() - ts) * 1000
            logger.info(f'{COMPUTE_BACKEND} build image - elaps={elaps:.2f}ms')

    # Limit ressources
    memory_limit_mb = f'{get_memory_limit()}M'
    cpu_set, gpu_set = get_cpu_gpu_sets()    # blocking call

    logger.info(f'Launch container {job_name} with {cpu_set} CPU - {gpu_set} GPU - {memory_limit_mb}.')

    BACKEND[COMPUTE_BACKEND]['compute'](
        image_name,
        job_name,
        cpu_set,
        memory_limit_mb,
        command,
        volumes,
        TASK_LABEL,
        capture_logs,
        environment,
        gpu_set,
        remove_image,
        subtuple_key=subtuple_key
    )


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

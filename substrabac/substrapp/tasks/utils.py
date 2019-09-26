import os
import docker
import GPUtil as gputil
import threading
import time

import logging

from subprocess import check_output
from django.conf import settings
from requests.auth import HTTPBasicAuth
from substrapp.utils import get_owner, get_remote_file, NodeError


DOCKER_LABEL = 'substra_task'

logger = logging.getLogger(__name__)


def authenticate_worker(node_id):
    from node.models import OutgoingNode

    owner = get_owner()

    # This handle worker node authentication
    # WARN: This should use a different authentication
    #       Backend (WorkerBackend for example) to be able
    #       to differentiate regular node users from workers
    if node_id == owner:
        auth = HTTPBasicAuth(settings.BASICAUTH_USERNAME, settings.BASICAUTH_PASSWORD)
    else:
        try:
            outgoing = OutgoingNode.objects.get(node_id=node_id)
        except OutgoingNode.DoesNotExist:
            raise NodeError(f'Unauthorized to call node_id: {node_id}')

        auth = HTTPBasicAuth(owner, outgoing.secret)

    return auth


def get_asset_content(url, node_id, content_hash, salt=None):
    return get_remote_file(url, authenticate_worker(node_id), content_hash, salt=salt)


def get_cpu_sets(cpu_count, concurrency):
    cpu_step = max(1, cpu_count // concurrency)
    cpu_sets = []

    for cpu_start in range(0, cpu_count, cpu_step):
        cpu_set = f'{cpu_start}-{min(cpu_start + cpu_step - 1, cpu_count - 1)}'
        cpu_sets.append(cpu_set)
        if len(cpu_sets) == concurrency:
            break

    return cpu_sets


def get_gpu_sets(gpu_list, concurrency):

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


def update_statistics(task_statistics, stats, gpu_stats):

    # CPU

    if stats is not None:

        if 'cpu_stats' in stats and stats['cpu_stats']['cpu_usage'].get('total_usage', None):
            # Compute CPU usage in %
            delta_total_usage = (stats['cpu_stats']['cpu_usage']['total_usage'] -
                                 stats['precpu_stats']['cpu_usage']['total_usage'])
            delta_system_usage = (stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage'])
            total_usage = (delta_total_usage / delta_system_usage) * stats['cpu_stats']['online_cpus'] * 100.0

            task_statistics['cpu']['current'].append(total_usage)
            task_statistics['cpu']['max'] = max(task_statistics['cpu']['max'],
                                                max(task_statistics['cpu']['current']))

        # MEMORY in GB
        if 'memory_stats' in stats:
            current_usage = stats['memory_stats'].get('usage', None)
            max_usage = stats['memory_stats'].get('max_usage', None)

            if current_usage:
                task_statistics['memory']['current'].append(current_usage / 1024**3)
            if max_usage:
                task_statistics['memory']['max'] = max(task_statistics['memory']['max'],
                                                       max_usage / 1024**3,
                                                       max(task_statistics['memory']['current']))

        # Network in kB
        if 'networks' in stats:
            task_statistics['netio']['rx'] = stats['networks']['eth0'].get('rx_bytes', 0)
            task_statistics['netio']['tx'] = stats['networks']['eth0'].get('tx_bytes', 0)

    # GPU

    if gpu_stats is not None:
        total_usage = sum([100 * gpu.load for gpu in gpu_stats])
        task_statistics['gpu']['current'].append(total_usage)
        task_statistics['gpu']['max'] = max(task_statistics['gpu']['max'],
                                            max(task_statistics['gpu']['current']))

        total_usage = sum([gpu.memoryUsed for gpu in gpu_stats]) / 1024
        task_statistics['gpu_memory']['current'].append(total_usage)
        task_statistics['gpu_memory']['max'] = max(task_statistics['gpu_memory']['max'],
                                                   max(task_statistics['gpu_memory']['current']))


def monitoring_task(client, task_args):
    """thread worker function"""

    task_name = task_args['name']

    gpu_set = None
    if 'environment' in task_args:
        gpu_set = task_args['environment']['NVIDIA_VISIBLE_DEVICES']

    start = time.time()
    t = threading.currentThread()

    # Statistics
    task_statistics = {'memory': {'max': 0,
                                  'current': [0]},
                       'gpu_memory': {'max': 0,
                                      'current': [0]},
                       'cpu': {'max': 0,
                               'current': [0]},
                       'gpu': {'max': 0,
                               'current': []},
                       'io': {'max': 0,
                              'current': []},
                       'netio': {'rx': 0,
                                 'tx': 0},
                       'time': 0}

    while not t.stopthread.isSet():
        stats = None
        try:
            container = client.containers.get(task_name)
            stats = container.stats(decode=True, stream=False)
        except (docker.errors.NotFound, docker.errors.APIError):
            pass

        gpu_stats = None
        if gpu_set is not None:
            gpu_stats = [gpu for gpu in gputil.getGPUs() if str(gpu.id) in gpu_set]

        update_statistics(task_statistics, stats, gpu_stats)

    task_statistics['time'] = time.time() - start

    t._stats = task_statistics

    t._result = f"CPU:{t._stats['cpu']['max']:.2f} % - Mem:{t._stats['memory']['max']:.2f}"
    t._result += f" GB - GPU:{t._stats['gpu']['max']:.2f} % - GPU Mem:{t._stats['gpu_memory']['max']:.2f} GB"


def container_format_log(container_name, container_logs):
    logs = [f'[{container_name}] {log}' for log in container_logs.decode().split('\n')]
    for log in logs:
        logger.info(log)


def compute_docker(client, resources_manager, dockerfile_path, image_name, container_name, volumes, command,
                   remove_image=True, remove_container=True, capture_logs=True):

    dockerfile_fullpath = os.path.join(dockerfile_path, 'Dockerfile')
    if not os.path.exists(dockerfile_fullpath):
        raise Exception(f'Dockerfile does not exist : {dockerfile_fullpath}')

    # Build metrics
    try:
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

    # Limit ressources
    memory_limit_mb = f'{resources_manager.memory_limit_mb()}M'
    cpu_set, gpu_set = resources_manager.get_cpu_gpu_sets()    # blocking call

    task_args = {'image': image_name,
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
                 'cap_drop': ['ALL']}

    if gpu_set is not None:
        task_args['environment'] = {'NVIDIA_VISIBLE_DEVICES': gpu_set}
        task_args['runtime'] = 'nvidia'

    task = ExceptionThread(target=client.containers.run,
                           kwargs=task_args)

    monitoring = ExceptionThread(target=monitoring_task,
                                 args=(client, task_args))

    task.start()
    monitoring.start()

    task.join()
    monitoring.join()

    # Remove container in all case (exception thrown or not)
    # We already get the excetion and we need to remove the containers to be able to remove the local
    # volume in case of fl task.
    container = client.containers.get(container_name)
    if capture_logs:
        container_format_log(
            container_name,
            container.logs()
        )

    if remove_container:
        container.remove()

    # Remove images
    if remove_image or hasattr(task, "_exception"):
        client.images.remove(image_name, force=True)

    if hasattr(task, "_exception"):
        raise task._exception

    return monitoring._result


class ExceptionThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(ExceptionThread, self).__init__(*args, **kwargs)
        self.stopthread = threading.Event()

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

    def join(self, timeout=None):
        self.stopthread.set()
        super(ExceptionThread, self).join(timeout)


class ResourcesManager():

    __concurrency = int(getattr(settings, 'CELERY_WORKER_CONCURRENCY'))
    __cpu_count = os.cpu_count()
    __cpu_sets = get_cpu_sets(__cpu_count, __concurrency)

    # Set CUDA_DEVICE_ORDER so the IDs assigned by CUDA match those from nvidia-smi
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    __gpu_list = [str(gpu.id) for gpu in gputil.getGPUs()]
    __gpu_sets = get_gpu_sets(__gpu_list, __concurrency)  # Can be None if no gpu

    __lock = threading.Lock()
    __docker = docker.from_env()

    @classmethod
    def memory_limit_mb(cls):
        try:
            return int(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024. ** 2)) // cls.__concurrency
        except ValueError:
            # fixes macOS issue https://github.com/SubstraFoundation/substrabac/issues/262
            return int(check_output(['sysctl', '-n', 'hw.memsize']).strip()) // cls.__concurrency

    @classmethod
    def get_cpu_gpu_sets(cls):

        cpu_set = None
        gpu_set = None

        with cls.__lock:
            # We can just wait for cpu because cpu and gpu is allocated the same way
            while cpu_set is None:

                # Get ressources used
                filters = {'status': 'running',
                           'label': [DOCKER_LABEL]}

                try:
                    containers = [container.attrs
                                  for container in cls.__docker.containers.list(filters=filters)]
                except docker.errors.APIError as e:
                    logger.error(e, exc_info=True)
                    continue

                # CPU
                used_cpu_sets = [container['HostConfig']['CpusetCpus']
                                 for container in containers
                                 if container['HostConfig']['CpusetCpus']]

                cpu_sets_available = filter_cpu_sets(used_cpu_sets, cls.__cpu_sets)

                if cpu_sets_available:
                    cpu_set = cpu_sets_available.pop()

                # GPU
                if cls.__gpu_sets is not None:
                    env_containers = [container['Config']['Env']
                                      for container in containers]

                    used_gpu_sets = []

                    for env_list in env_containers:
                        nvidia_env_var = [s.split('=')[1]
                                          for s in env_list if "NVIDIA_VISIBLE_DEVICES" in s]

                        used_gpu_sets.extend(nvidia_env_var)

                    gpu_sets_available = filter_gpu_sets(used_gpu_sets, cls.__gpu_sets)

                    if gpu_sets_available:
                        gpu_set = gpu_sets_available.pop()

        return cpu_set, gpu_set

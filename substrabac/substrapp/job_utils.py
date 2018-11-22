import os
import GPUtil as gputil
import threading
import time


def get_cpu_sets(cpu_count, concurrency):
    cpu_step = max(1, cpu_count // concurrency)
    cpu_sets = []

    for cpu_start in range(0, cpu_count, cpu_step):
        cpu_set = '%s-%s' % (cpu_start, min(cpu_start + cpu_step - 1, cpu_count - 1))
        cpu_sets.append(cpu_set)
        if len(cpu_sets) == concurrency:
            break

    return cpu_sets


def get_gpu_sets(gpu_list, concurrency):
    gpu_count = len(gpu_list)
    gpu_step = max(1, gpu_count // concurrency)
    gpu_sets = []

    for igpu_start in range(0, gpu_count, gpu_step):
        gpu_sets.append(','.join(gpu_list[igpu_start: igpu_start + gpu_step]))

    return gpu_sets


def update_statistics(job_statistics, stats, gpu_stats):

    # CPU

    if stats is not None:

        if 'cpu_stats' in stats and stats['cpu_stats']['cpu_usage'].get('total_usage', None):
            # Compute CPU usage in %
            delta_total_usage = (stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage'])
            delta_system_usage = (stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage'])
            total_usage = (delta_total_usage / delta_system_usage) * stats['cpu_stats']['online_cpus'] * 100.0

            job_statistics['cpu']['current'].append(total_usage)
            job_statistics['cpu']['max'] = max(job_statistics['cpu']['max'],
                                               max(job_statistics['cpu']['current']))

        # MEMORY in GB
        if 'memory_stats' in stats:
            current_usage = stats['memory_stats'].get('usage', None)
            max_usage = stats['memory_stats'].get('max_usage', None)

            if current_usage:
                job_statistics['memory']['current'].append(current_usage / 1024**3)
            if max_usage:
                job_statistics['memory']['max'] = max(job_statistics['memory']['max'],
                                                      max_usage / 1024**3,
                                                      max(job_statistics['memory']['current']))

        # Network in kB
        if 'networks' in stats:
            job_statistics['netio']['rx'] = stats['networks']['eth0'].get('rx_bytes', 0)
            job_statistics['netio']['tx'] = stats['networks']['eth0'].get('tx_bytes', 0)

    # GPU

    if gpu_stats is not None:
        total_usage = sum([100 * gpu.load for gpu in gpu_stats])
        job_statistics['gpu']['current'].append(total_usage)
        job_statistics['gpu']['max'] = max(job_statistics['gpu']['max'],
                                           max(job_statistics['gpu']['current']))

        total_usage = sum([gpu.memoryUsed for gpu in gpu_stats]) / 1024
        job_statistics['gpu_memory']['current'].append(total_usage)
        job_statistics['gpu_memory']['max'] = max(job_statistics['gpu_memory']['max'],
                                                  max(job_statistics['gpu_memory']['current']))

    # IO DISK
    # "blkio_stats": {
    #   "io_service_bytes_recursive": [],
    #   "io_serviced_recursive": [],
    #   "io_queue_recursive": [],
    #   "io_service_time_recursive": [],
    #   "io_wait_time_recursive": [],
    #   "io_merged_recursive": [],
    #   "io_time_recursive": [],
    #   "sectors_recursive": []
    # }

    # LOGGING
    # printable_stats = 'CPU - now : %d %% / max : %d %% | MEM - now : %.2f GB / max : %.2f GB' % \
    #     (job_statistics['cpu']['current'][-1],
    #      job_statistics['cpu']['max'],
    #      job_statistics['memory']['current'][-1],
    #      job_statistics['memory']['max'])

    # logging.info('[JOB] Monitoring : %s' % (printable_stats, ))


def monitoring_job(client, job_args):
    """thread worker function"""

    job_name = job_args['name']

    gpu_set = None
    if 'environment' in job_args:
        gpu_set = job_args['environment']['NVIDIA_VISIBLE_DEVICES']

    start = time.time()
    t = threading.currentThread()

    # Statistics
    job_statistics = {'memory': {'max': 0,
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

    while getattr(t, "do_run", True):
        stats = None
        try:
            container = client.containers.get(job_name)
            stats = container.stats(decode=True, stream=False)
        except:
            pass

        gpu_stats = None
        if gpu_set is not None:
            gpu_stats = [gpu for gpu in gputil.getGPUs() if str(gpu.id) in gpu_set]

        update_statistics(job_statistics, stats, gpu_stats)

    job_statistics['time'] = time.time() - start

    t._result = 'CPU:%.2f %% - Mem:%.2f GB - GPU:%.2f %% - GPU Mem:%.2f GB' % (job_statistics['cpu']['max'],
                                                                               job_statistics['memory']['max'],
                                                                               job_statistics['gpu']['max'],
                                                                               job_statistics['gpu_memory']['max'])

    t._stats = job_statistics


def compute_docker(client, ressource_manager, dockerfile_path, image_name, container_name, volumes, command, cpu_set, gpu_set):

    # Build metrics
    client.images.build(path=dockerfile_path,
                        tag=image_name,
                        rm=True)
    cpu_set = None
    gpu_set = None

    mem_limit = ressource_manager.memory_limit_mb()

    while cpu_set is None or gpu_set is None:
        cpu_set = ressource_manager.acquire_cpu_set()
        gpu_set = ressource_manager.acquire_gpu_set()
        time.sleep(2)

    job_args = {'image': image_name,
                'name': container_name,
                'cpuset_cpus': cpu_set,
                'mem_limit': mem_limit,
                'command': command,
                'volumes': volumes,
                'detach': False,
                'auto_remove': False,
                'remove': False}

    if gpu_set != 'no_gpu':
        job_args['environment'] = {'NVIDIA_VISIBLE_DEVICES': gpu_set}
        job_args['runtime'] = 'nvidia'

    job = ExceptionThread(target=client.containers.run,
                          kwargs=job_args)
    monitoring = ExceptionThread(target=monitoring_job, args=(client, job_args))

    job.start()
    monitoring.start()

    job.join()
    monitoring.do_run = False
    monitoring.join()

    # Return ressources
    ressource_manager.return_cpu_set(cpu_set)
    ressource_manager.return_gpu_set(gpu_set)

    cpu_set = None
    gpu_set = None

    if hasattr(job, "_exception"):
        raise job._exception

    # Remove only if container exit without exception
    container = client.containers.get(container_name)
    container.remove()

    return monitoring._result


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


class RessourceManager():
    __concurrency = int(os.environ.get('CELERYD_CONCURRENCY', 1))
    __memory_gb = int(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024. ** 2))

    __cpu_count = os.cpu_count()
    __cpu_sets = get_cpu_sets(__cpu_count, __concurrency)

    # Set CUDA_DEVICE_ORDER so the IDs assigned by CUDA match those from nvidia-smi
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    __gpu_list = [str(gpu.id) for gpu in gputil.getGPUs()]

    __gpu_sets = 'no_gpu'
    if __gpu_list:
        __gpu_sets = get_gpu_sets(__gpu_list, __concurrency)

    __used_cpu_sets = []
    __used_gpu_sets = []
    __lock = threading.Lock()

    @classmethod
    def memory_limit_mb(cls):
        return '%sM' % (cls.__memory_gb // cls.__concurrency)

    @classmethod
    def acquire_cpu_set(cls):
        cpu_set = None
        cls.__lock.acquire()

        try:
            cpu_set_available = set(cls.__cpu_sets).difference(set(cls.__used_cpu_sets))
            if len(cpu_set_available) > 0:
                cpu_set = cpu_set_available.pop()
                cls.__used_cpu_sets.append(cpu_set)
        except:
            pass

        cls.__lock.release()
        return cpu_set

    @classmethod
    def return_cpu_set(cls, cpu_set):
        cls.__lock.acquire()

        try:
            cls.__used_cpu_sets.remove(cpu_set)
        except:
            pass

        cls.__lock.release()

    @classmethod
    def acquire_gpu_set(cls):
        gpu_set = 'no_gpu'
        cls.__lock.acquire()

        if cls.__gpu_sets != 'no_gpu':
            gpu_set = None
            try:
                gpu_set_available = set(cls.__gpu_sets).difference(set(cls.__used_gpu_sets))
                if len(gpu_set_available) > 0:
                    gpu_set = gpu_set_available.pop()
                    cls.__used_gpu_sets.append(gpu_set)
            except:
                pass

        cls.__lock.release()
        return gpu_set

    @classmethod
    def return_gpu_set(cls, gpu_set):
        cls.__lock.acquire()

        if gpu_set != 'no_gpu':
            try:
                cls.__used_gpu_sets.remove(gpu_set)
            except:
                pass

        cls.__lock.release()

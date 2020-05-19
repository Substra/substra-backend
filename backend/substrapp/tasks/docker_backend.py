import docker
import time

import logging
logger = logging.getLogger(__name__)


def docker_memory_limit(celery_worker_concurrency, celeryworker_image):
    docker_client = docker.from_env()
    # Get memory limit from docker container through the API
    # Because the docker execution may be remote

    cmd = f'python3 -u -c "import os; print(int(os.sysconf("SC_PAGE_SIZE") '\
          f'* os.sysconf("SC_PHYS_PAGES") / (1024. ** 2)) // {celery_worker_concurrency}), end=\'\')"'

    task_args = {
        'image': celeryworker_image,
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


def docker_cpu_count(celeryworker_image):
    docker_client = docker.from_env()
    # Get CPU count from docker container through the API
    # Because the docker execution may be remote

    task_args = {
        'image': celeryworker_image,
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

    cpu_count_bytes = docker_client.containers.run(**task_args).strip()

    return cpu_count_bytes


def docker_gpu_list(celeryworker_image):
    docker_client = docker.from_env()
    # Get GPU list from docker container through the API
    # Because the docker execution may be remote

    cmd = 'python3 -u -c "import GPUtil as gputil;import json;'\
          'print(json.dumps([str(gpu.id) for gpu in gputil.getGPUs()]), end=\'\')"'

    task_args = {
        'image': celeryworker_image,
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

    gpu_list_bytes = docker_client.containers.run(**task_args)

    return gpu_list_bytes


def docker_cpu_used(task_label):
    docker_client = docker.from_env()
    # Get CPU used from docker container through the API
    # Because the docker execution may be remote

    filters = {'status': 'running',
               'label': [task_label]}

    containers = [container.attrs
                  for container in docker_client.containers.list(filters=filters)]

    used_cpu_sets = [container['HostConfig']['CpusetCpus']
                     for container in containers
                     if container['HostConfig']['CpusetCpus']]

    return used_cpu_sets


def docker_gpu_used(task_label):
    docker_client = docker.from_env()
    # Get GPU used from docker container through the API
    # Because the docker execution may be remote

    filters = {'status': 'running',
               'label': [task_label]}

    containers = [container.attrs
                  for container in docker_client.containers.list(filters=filters)]

    env_containers = [container['Config']['Env']
                      for container in containers]

    used_gpu_sets = []

    for env_list in env_containers:
        nvidia_env_var = [s.split('=')[1]
                          for s in env_list if "NVIDIA_VISIBLE_DEVICES" in s]

        used_gpu_sets.extend(nvidia_env_var)

    return used_gpu_sets


def container_format_log(container_name, container_logs):
    logs = [f'[{container_name}] {log}' for log in container_logs.decode().split('\n')]
    for log in logs:
        logger.info(log)


def docker_build_image(path, tag, rm):
    docker_client = docker.from_env()
    return docker_client.images.build(path=path, tag=tag, rm=rm)


def docker_get_image(image_name):
    docker_client = docker.from_env()
    return docker_client.images.get(image_name)


def docker_get_or_create_local_volume(volume_id):

    docker_client = docker.from_env()

    try:
        docker_client.volumes.get(volume_id=volume_id)
    except docker.errors.NotFound:
        docker_client.volumes.create(name=volume_id)


def docker_remove_local_volume(volume_id):

    docker_client = docker.from_env()

    try:
        local_volume = docker_client.volumes.get(volume_id=volume_id)
        local_volume.remove(force=True)
    except docker.errors.NotFound:
        pass
    except Exception:
        logger.error(f'Cannot remove volume {volume_id}', exc_info=True)


def docker_remove_image(image_name):
    docker_client = docker.from_env()
    try:
        if docker_client.images.get(image_name):
            logger.info(f'Remove docker image {image_name}')
            docker_client.images.remove(image_name, force=True)

    except docker.errors.ImageNotFound:
        pass
    except docker.errors.APIError as e:
        logger.exception(e)


def docker_compute(image_name, job_name, cpu_set, memory_limit_mb, command, volumes, task_label,
                   capture_logs, environment, gpu_set, remove_image):

    docker_client = docker.from_env()

    task_args = {
        'image': image_name,
        'name': job_name,
        'cpuset_cpus': cpu_set,
        'mem_limit': memory_limit_mb,
        'command': command,
        'volumes': volumes,
        'shm_size': '8G',
        'labels': [task_label],
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
        docker_client.containers.run(**task_args)
    finally:
        # we need to remove the containers to be able to remove the local
        # volume in case of compute plan
        container = docker_client.containers.get(job_name)
        if capture_logs:
            container_format_log(
                job_name,
                container.logs()
            )
        container.remove()

        # Remove images
        if remove_image:
            docker_client.images.remove(image_name, force=True)

        elaps = (time.time() - ts) * 1000
        logger.info(f'docker_client.images.run - elaps={elaps:.2f}ms')

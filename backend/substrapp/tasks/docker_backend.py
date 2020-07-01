import docker
import GPUtil
from substrapp.utils import timeit

import logging
logger = logging.getLogger(__name__)


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


@timeit
def docker_compute(image_name, job_name, command, volumes, task_label,
                   capture_logs, environment, remove_image, subtuple_key, compute_plan_id):

    docker_client = docker.from_env()

    task_args = {
        'image': image_name,
        'name': job_name,
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

    if GPUtil.getGPUs():
        task_args['environment'].update({'CUDA_DEVICE_ORDER': 'PCI_BUS_ID'})
        task_args['environment'].update({'NVIDIA_VISIBLE_DEVICES': 'all'})
        task_args['runtime'] = 'nvidia'

    try:
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

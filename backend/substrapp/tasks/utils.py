import os
import json
import logging
import functools
import threading

from django.conf import settings
from requests.auth import HTTPBasicAuth
from substrapp.utils import get_owner, get_remote_file_content, get_and_put_remote_file_content, NodeError, timeit

from substrapp.tasks.k8s_backend import (
    k8s_get_image, k8s_build_image, k8s_remove_local_volume, k8s_get_or_create_local_volume,
    k8s_remove_image, k8s_compute, ImageNotFound, BuildError)


CELERYWORKER_IMAGE = os.environ.get('CELERYWORKER_IMAGE', 'substrafoundation/celery:latest')
CELERY_WORKER_CONCURRENCY = int(getattr(settings, 'CELERY_WORKER_CONCURRENCY'))
TASK_LABEL = 'substra_task'
BUILD_IMAGE = settings.TASK['BUILD_IMAGE']

logger = logging.getLogger(__name__)


def authenticate_worker(node_id):
    from node.models import OutgoingNode

    owner = get_owner()

    try:
        outgoing = OutgoingNode.objects.get(node_id=node_id)
    except OutgoingNode.DoesNotExist:
        raise NodeError(f'Unauthorized to call node_id: {node_id}')

    auth = HTTPBasicAuth(owner, outgoing.secret)

    return auth


def get_asset_content(channel_name, url, node_id, content_hash, salt=None):
    return get_remote_file_content(channel_name, url, authenticate_worker(node_id), content_hash, salt=salt)


def get_and_put_asset_content(channel_name, url, node_id, content_hash, content_dst_path, hash_key):
    return get_and_put_remote_file_content(channel_name, url, authenticate_worker(node_id), content_hash,
                                           content_dst_path=content_dst_path, hash_key=hash_key)


def path_to_dict(path):
    d = {'name': os.path.basename(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [path_to_dict(os.path.join(path, x)) for x in os.listdir(path)]
    else:
        d['type'] = "file"
    return d


def list_files(startpath, as_json=True):
    if not settings.TASK['LIST_WORKSPACE']:
        return 'Error: listing files is disabled.'

    if not os.path.exists(startpath):
        return f'Error: {startpath} does not exist.'

    if as_json:
        return json.dumps(path_to_dict(startpath))

    res = ''
    for root, dirs, files in os.walk(startpath, followlinks=True):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        res += f'{indent}{os.path.basename(root)}/' + "\n"
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            res += f'{subindent}{f}' + "\n"

    return res


def get_or_create_local_volume(volume_id):
    return k8s_get_or_create_local_volume(volume_id)


def remove_local_volume(volume_id):
    return k8s_remove_local_volume(volume_id)


def remove_image(image_name):
    return k8s_remove_image(image_name)


def raise_if_no_dockerfile(dockerfile_path):
    dockerfile_fullpath = os.path.join(dockerfile_path, 'Dockerfile')
    if not os.path.exists(dockerfile_fullpath):
        raise Exception(f'Dockerfile does not exist : {dockerfile_fullpath}')


def container_format_log(container_name, container_logs):
    logs = [f'[{container_name}] {log}' for log in container_logs.decode().split('\n')]
    for log in logs:
        logger.info(log)


@timeit
def compute_job(subtuple_key, compute_plan_id, dockerfile_path, image_name, job_name, volumes, command,
                environment, remove_image=True, remove_container=True, capture_logs=True):

    raise_if_no_dockerfile(dockerfile_path)

    build_image = BUILD_IMAGE

    # Check if image already exist
    try:
        k8s_get_image(image_name)
    except ImageNotFound:
        if build_image:
            logger.info(f'Image not found: {image_name}. Building it.')
        else:
            logger.info(f'Image not found: {image_name}')
    else:
        logger.info(f'Image found: {image_name}. Using it.')
        build_image = False

    if build_image:
        try:
            k8s_build_image(
                path=dockerfile_path,
                tag=image_name,
                rm=remove_image)
        except BuildError as e:
            error = '\n' + str(e)
            logger.error(f'Build error: {error}')
            raise

    k8s_compute(
        image_name,
        job_name,
        command,
        volumes,
        TASK_LABEL,
        capture_logs,
        environment,
        remove_image,
        subtuple_key=subtuple_key,
        compute_plan_id=compute_plan_id
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

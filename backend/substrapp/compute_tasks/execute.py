"""
This file contains the function execution part of a compute task.

In these functions, we:
- Determine the command to execute (train/test/eval)
- Create the compute pod, if necessary
- Execute the command in the compute pod
"""

import io
from typing import Optional

import kubernetes
import structlog
from django.conf import settings

from orchestrator import get_orchestrator_client
from substrapp import docker_registry
from substrapp.compute_tasks import compute_task as task_utils
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.compute_tasks import image_builder
from substrapp.compute_tasks import utils
from substrapp.compute_tasks.command import get_exec_command
from substrapp.compute_tasks.command import get_exec_command_args
from substrapp.compute_tasks.command import write_command_args_file
from substrapp.compute_tasks.compute_pod import ComputePod
from substrapp.compute_tasks.compute_pod import Label
from substrapp.compute_tasks.compute_pod import create_pod
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.environment import get_environment
from substrapp.compute_tasks.image_builder import push_blob_to_registry
from substrapp.compute_tasks.volumes import get_volumes
from substrapp.compute_tasks.volumes import get_worker_subtuple_pvc_name
from substrapp.exceptions import OrganizationError
from substrapp.exceptions import OrganizationHttpError
from substrapp.exceptions import PodReadinessTimeoutError
from substrapp.kubernetes_utils import delete_pod
from substrapp.kubernetes_utils import execute
from substrapp.kubernetes_utils import get_volume
from substrapp.kubernetes_utils import pod_exists_by_label_selector
from substrapp.kubernetes_utils import wait_for_pod_readiness
from substrapp.models import FunctionImage
from substrapp.models import ImageEntrypoint
from substrapp.utils import timeit

logger = structlog.get_logger(__name__)


def _is_pod_creation_needed(label_selector: str, *, client: Optional[kubernetes.client.CoreV1Api] = None) -> bool:
    if not client:
        client = _get_k8s_client()

    return not pod_exists_by_label_selector(client, label_selector)


def _is_function_image_downloaded(function_key: str) -> bool:
    try:
        FunctionImage.objects.get(function_id=function_key)
        return True
    except FunctionImage.DoesNotExist:
        return False


@timeit
def download_function(ctx: Context) -> None:
    channel_name = ctx.channel_name
    container_image_tag = utils.container_image_tag_from_function(ctx.function)
    compute_pod = ctx.get_compute_pod(container_image_tag)

    if not _is_function_image_downloaded(ctx.function.key) and _is_pod_creation_needed(compute_pod.label_selector):
        try:
            image_builder.load_remote_function_image(ctx.function, channel_name)
        except OrganizationHttpError as e:
            raise compute_task_errors.CeleryNoRetryError() from e
        except OrganizationError as e:
            raise compute_task_errors.CeleryRetryError() from e


@timeit
def execute_compute_task(ctx: Context) -> None:
    channel_name = ctx.channel_name
    container_image_tag = utils.container_image_tag_from_function(ctx.function)

    compute_pod = ctx.get_compute_pod(container_image_tag)
    pod_name = compute_pod.name

    env = get_environment(ctx)
    image = docker_registry.get_container_image_name(container_image_tag)

    k8s_client = _get_k8s_client()

    if _is_pod_creation_needed(compute_pod.label_selector, client=k8s_client):
        # save entrypoint to DB
        try:
            entrypoint = docker_registry.get_entrypoint(container_image_tag)
        except docker_registry.ImageNotFoundError:
            # push the image from the saved binary blob
            container_image_tag = utils.container_image_tag_from_function(ctx.function)
            function_image_fd = FunctionImage.objects.get(function_id=ctx.function.key).file.open("rb").read()
            push_blob_to_registry(function_image_fd, container_image_tag)
            entrypoint = docker_registry.get_entrypoint(container_image_tag)
        ImageEntrypoint.objects.get_or_create(
            archive_checksum=ctx.function.archive_address.checksum, entrypoint_json=entrypoint
        )
        volume_mounts, volumes = get_volumes(ctx)

        with get_orchestrator_client(channel_name) as client:
            # Only create the pod if the compute plan hasn't been cancelled by a concurrent process.
            # We use allow_executing=True to allow celery retries.
            task_utils.abort_task_if_not_runnable(ctx.task.key, client, allow_executing=True)

        create_pod(k8s_client, compute_pod, pod_name, image, env, volume_mounts, volumes)
        try:
            wait_for_pod_readiness(
                k8s_client, f"{Label.PodName}={pod_name}", settings.TASK["COMPUTE_POD_STARTUP_TIMEOUT_SECONDS"]
            )
        except PodReadinessTimeoutError:
            delete_pod(k8s_client, pod_name)
            raise
    else:
        logger.info("Reusing pod", pod=pod_name)

    # This a sanity check that the compute pod uses the subtuple of the present worker
    # Does not concern the WORKER_PVC_IS_HOSTPATH case because this case is for a single worker set up.
    if not settings.WORKER_PVC_IS_HOSTPATH:
        _check_compute_pod_and_worker_share_same_subtuple(k8s_client, pod_name)  # can raise

    _exec(ctx, compute_pod)


def _get_k8s_client() -> kubernetes.client.CoreV1Api:
    kubernetes.config.load_incluster_config()
    return kubernetes.client.CoreV1Api()


def _check_compute_pod_and_worker_share_same_subtuple(k8s_client: kubernetes.client.CoreV1Api, pod_name: str) -> None:
    # This a sanity check that the compute pod uses the subtuple of the present worker.
    # The contrary should never happen as _acquire_worker_index in backend/substrapp/task_routing.py
    # is ensuring that the right worker is assigned.
    # This check is here for a faster debugging if something is going wrong.
    subtuple_volume = get_volume(k8s_client, pod_name, "subtuple")

    if not subtuple_volume:
        raise Exception("no subtuple volume is attached to compute pod")

    compute_pod_subtuple_claim_name = subtuple_volume.persistent_volume_claim.claim_name
    worker_subtuple_claim_name = get_worker_subtuple_pvc_name()

    if compute_pod_subtuple_claim_name != worker_subtuple_claim_name:
        raise Exception(
            f"This worker and the compute pod {pod_name} do not share the same "
            "subtuple volume. It will not be possible for the task to retrieve the data."
        )


@timeit
def _exec(ctx: Context, compute_pod: ComputePod):
    """Execute a command on a compute pod"""

    command = get_exec_command(ctx)
    command_args = get_exec_command_args(ctx)

    logger.debug("Running command", command=command, command_args=command_args)

    write_command_args_file(ctx.directories, command_args)
    resp = execute(compute_pod.name, command)

    def print_log(lines):
        for line in filter(None, lines.split("\n")):
            logger.info(line)

    container_logs = io.BytesIO()

    while resp.is_open():
        resp.update(timeout=1)
        if resp.peek_stdout():
            read = resp.read_stdout()
            print_log(read)
            container_logs.write(read.encode())

    resp.close()

    # resp.returncode must only be called once, see https://github.com/kubernetes-client/python-base/issues/271
    returncode = resp.returncode

    if returncode != 0:
        raise compute_task_errors.ExecutionError(
            container_logs, f"Error running compute task. Compute task process exited with code {returncode}"
        )

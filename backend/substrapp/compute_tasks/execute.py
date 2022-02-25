"""
This file contains the algo/metrics execution part of a compute task.

In these functions, we:
- Determine the command to execute (train/test/eval)
- Create the compute pod, if necessary
- Execute the command in the compute pod
"""
import io
from typing import List

import kubernetes
import structlog
from django.conf import settings
from kubernetes.stream import stream

import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.compute_tasks.command import get_exec_command
from substrapp.compute_tasks.compute_pod import ComputePod
from substrapp.compute_tasks.compute_pod import Label
from substrapp.compute_tasks.compute_pod import create_pod
from substrapp.compute_tasks.compute_task import is_task_runnable
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.environment import get_environment
from substrapp.compute_tasks.volumes import get_volumes
from substrapp.compute_tasks.volumes import get_worker_subtuple_pvc_name
from substrapp.docker_registry import get_container_image_name
from substrapp.exceptions import PodError
from substrapp.exceptions import PodReadinessTimeoutError
from substrapp.exceptions import PodTimeoutError
from substrapp.kubernetes_utils import delete_pod
from substrapp.kubernetes_utils import get_volume
from substrapp.kubernetes_utils import pod_exists_by_label_selector
from substrapp.kubernetes_utils import wait_for_pod_readiness
from substrapp.utils import timeit

logger = structlog.get_logger(__name__)

NAMESPACE = settings.NAMESPACE


@timeit
def execute_compute_task(ctx: Context) -> None:

    _execute_compute_task(ctx, is_testtuple_eval=False)

    # Testtuple evaluation
    #
    # The execution of compute tasks of type testtuple is split into 2 steps:
    #
    # - The "predict" step which happens with is_testtuple_eval=False.
    # - The "evaluate" step, which happens with is_testtuple_eval=True
    #
    # The two steps are executed using different pods:
    #
    # - The "predict" step uses the algo container image. It outputs a prediction file.
    # - The "evaluate" step uses the metrics container image. It uses the prediction file as an input, and outputs
    #   a performance score. The "evaluate" step doesn't have access to data samples
    if ctx.task_category == computetask_pb2.TASK_TEST:
        for metric_key, metrics_image_tag in ctx.metrics_image_tags.items():
            _execute_compute_task(ctx, is_testtuple_eval=True, image_tag=metrics_image_tag, metric_key=metric_key)


@timeit
def _execute_compute_task(ctx: Context, is_testtuple_eval: bool, image_tag: str = None, metric_key: str = None) -> None:

    channel_name = ctx.channel_name
    dirs = ctx.directories
    image_tag = image_tag if is_testtuple_eval else ctx.algo_image_tag

    compute_pod = ctx.get_compute_pod(is_testtuple_eval, metric_key)
    pod_name = compute_pod.name

    env = get_environment(ctx)
    image = get_container_image_name(image_tag)
    exec_command = get_exec_command(ctx, is_testtuple_eval, metric_key)

    k8s_client = _get_k8s_client()

    try:
        should_create_pod = not pod_exists_by_label_selector(k8s_client, compute_pod.label_selector)

        if should_create_pod:

            volume_mounts, volumes = get_volumes(dirs, is_testtuple_eval)

            # Only create the pod if the compute plan hasn't been cancelled by a concurrent process.
            # We use allow_doing=True to allow celery retries.
            if not is_task_runnable(channel_name, ctx.task_key, allow_doing=True):
                raise Exception(
                    f"Gracefully aborting execution of task {ctx.task_key}. Task is not in a runnable state anymore."
                )

            create_pod(k8s_client, compute_pod, pod_name, image, env, volume_mounts, volumes)
            wait_for_pod_readiness(
                k8s_client, f"{Label.PodName}={pod_name}", settings.TASK["COMPUTE_POD_STARTUP_TIMEOUT_SECONDS"]
            )
        else:
            logger.info("Reusing pod", pod=pod_name)

        # This a sanity check that the compute pod uses the subtuple of the present worker
        # Does not concern the WORKER_PVC_IS_HOSTPATH case because this case is for a single worker set up.
        if not settings.WORKER_PVC_IS_HOSTPATH:
            _check_compute_pod_and_worker_share_same_subtuple(k8s_client, pod_name)  # can raise

        _exec(k8s_client, ctx, compute_pod, exec_command)

    except (PodError, PodTimeoutError) as e:
        logger.exception("failed to execute task", e=e)
        raise

    except PodReadinessTimeoutError as e:
        logger.exception(e)
        delete_pod(k8s_client, pod_name)
        raise

    except Exception as e:
        logger.exception(e)
        raise


def _get_k8s_client():
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
def _exec(k8s_client, ctx: Context, compute_pod: ComputePod, exec_command: List[str]):
    """Execute a command on a compute pod"""
    logger.debug("Running command", command=exec_command, eval=compute_pod.is_testtuple_eval, attempt=ctx.attempt)

    resp = stream(
        k8s_client.connect_get_namespaced_pod_exec,
        compute_pod.name,
        NAMESPACE,
        # use shell + redirection to ensure stdout/stderr are retrieved in order. Without this,
        # if the program outputs to both stdout and stderr at around the same time,
        # we lose the order of messages.
        command=["/bin/sh", "-c", " ".join(exec_command + ["2>&1"])],
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
        _preload_content=False,
    )

    def print_log(lines):
        for line in filter(None, lines.split("\n")):
            logger.info(line, eval=compute_pod.is_testtuple_eval, attempt=ctx.attempt)

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

"""
This file contains the algo/metrics execution part of a compute task.

In these functions, we:
- Determine the command to execute (train/test/eval)
- Create the compute pod, if necessary
- Execute the command in the compute pod
"""

from __future__ import absolute_import, unicode_literals

import logging
import kubernetes
from typing import Any, List
from django.conf import settings
from kubernetes.stream import stream
from substrapp.ledger.api import is_task_runnable
from substrapp.utils import timeit
from substrapp.compute_tasks.categories import (
    TASK_CATEGORY_TESTTUPLE,
)
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.command import get_exec_command
from substrapp.compute_tasks.environment import get_environment
from substrapp.compute_tasks.volumes import get_volumes
from substrapp.exceptions import PodError, PodReadinessTimeoutError, PodTimeoutError
from substrapp.kubernetes_utils import delete_pod, wait_for_pod_readiness, pod_exists_by_label_selector
from substrapp.docker_registry import get_container_image_name
from substrapp.compute_tasks.compute_pod import ComputePod, Label, create_pod

logger = logging.getLogger(__name__)

NAMESPACE = settings.NAMESPACE


@timeit
def execute_compute_task(ctx: Context) -> Any:

    result = _execute_compute_task(ctx, is_testtuple_eval=False)

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
    if ctx.task_category == TASK_CATEGORY_TESTTUPLE:
        result = _execute_compute_task(ctx, is_testtuple_eval=True)

    return result


@timeit
def _execute_compute_task(ctx: Context, is_testtuple_eval: bool) -> None:

    channel_name = ctx.channel_name
    dirs = ctx.directories
    compute_plan_key = ctx.compute_plan_key
    image_tag = ctx.metrics_image_tag if is_testtuple_eval else ctx.algo_image_tag

    compute_pod = ctx.get_compute_pod(is_testtuple_eval)
    pod_name = compute_pod.name

    env = get_environment(ctx)
    image = get_container_image_name(image_tag)
    exec_command = get_exec_command(ctx, is_testtuple_eval)

    k8s_client = _get_k8s_client()

    try:
        should_create_pod = not pod_exists_by_label_selector(k8s_client, compute_pod.label_selector)

        if should_create_pod:
            volume_mounts, volumes = get_volumes(dirs, is_testtuple_eval)

            # Only create the pod if the compute plan hasn't been cancelled by a concurrent process
            should_run = is_task_runnable(channel_name, ctx.task_key, ctx.task_category, ctx.compute_plan_key)
            if not should_run:
                raise Exception(
                    f"Gracefully aborting execution of task {ctx.task_key}. Task is not in a runnable state anymore."
                )

            create_pod(k8s_client, compute_pod, pod_name, image, env, volume_mounts, volumes)
            wait_for_pod_readiness(k8s_client, f"{Label.PodName}={pod_name}",
                                   settings.TASK["COMPUTE_POD_STARTUP_TIMEOUT_SECONDS"])
        else:
            logger.info(f"Reusing pod {pod_name}")

        returncode = _exec(k8s_client, ctx, compute_pod, exec_command)
        if returncode != 0:
            raise Exception(f"Error running compute task. Compute task process exited with code {returncode}")

    except (PodError, PodTimeoutError) as e:
        logger.error(e)
        raise

    except PodReadinessTimeoutError as e:
        logger.exception(e)
        delete_pod(k8s_client, pod_name)
        raise

    except Exception as e:
        logger.exception(e)
        raise

    finally:
        # TODO orchestrator: delete this condition
        if not compute_plan_key and not settings.DEBUG_KEEP_POD_AND_DIRS:
            delete_pod(k8s_client, pod_name)


def _get_k8s_client():
    kubernetes.config.load_incluster_config()
    return kubernetes.client.CoreV1Api()


@timeit
def _exec(k8s_client, ctx: Context, compute_pod: ComputePod, exec_command: List[str]) -> int:
    """Execute a command on a compute pod"""

    logger.debug(f"Running command {' '.join(exec_command)}")

    resp = stream(
        k8s_client.connect_get_namespaced_pod_exec,
        compute_pod.name,
        NAMESPACE,
        # use shell + redirection to ensure stdout/stderr are retrieved in order. Without this, if the program
        # outputs to both stdout and stderr at around the same time, we lose the order of messages.
        command=["/bin/sh", "-c", " ".join(exec_command + ["2>&1"])],
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
        _preload_content=False,
    )

    comp_or_eval = "e" if compute_pod.is_testtuple_eval else "c"
    log_prefix = f"[{ctx.compute_plan_key_safe[:8]}-{ctx.task_key[:8]}-{(comp_or_eval)}-{ctx.attempt}]"

    def print_log(lines):
        for line in filter(None, lines.split("\n")):
            logger.info(f"{log_prefix} {line}")

    while resp.is_open():
        resp.update(timeout=1)
        if resp.peek_stdout():
            print_log(resp.read_stdout())

    resp.close()
    return resp.returncode

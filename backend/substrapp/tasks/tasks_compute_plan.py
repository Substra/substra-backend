import typing

import structlog
from django.conf import settings

import orchestrator
from backend.celery import app
from substrapp.compute_tasks import utils
from substrapp.compute_tasks.compute_pod import delete_compute_plan_pods
from substrapp.compute_tasks.directories import Directories
from substrapp.compute_tasks.directories import teardown_compute_plan_dir
from substrapp.compute_tasks.lock import acquire_compute_plan_lock
from substrapp.docker_registry import delete_container_image_safe
from substrapp.orchestrator import get_orchestrator_client
from substrapp.task_routing import release_worker

logger = structlog.get_logger(__name__)


def queue_delete_cp_pod_and_dirs_and_optionally_images(
    channel_name: str, compute_plan: orchestrator.ComputePlan
) -> None:
    if settings.DEBUG_KEEP_POD_AND_DIRS:
        return

    from substrapp.task_routing import get_existing_worker_queue

    worker_queue = get_existing_worker_queue(compute_plan.key)

    if worker_queue is None:
        # Since we receive events for all compute tasks, including tasks that belong to compute plans which are
        # entirely executed in other organizations, there's no way to know if:
        # - this is expected behavior (there's no task for this CP on this org), or
        # - this is unexpected behavior (the mapping should have been created but never was)
        logger.debug(
            "The compute plan is finished but no action will be performed to delete the compute pods and teardown "
            "the compute plan dirs because the compute plan is not mapped to any worker. This is expected behavior "
            "in some cases, including: - This CP has no compute task ran on this organisation - Another process/task "
            "already called this function for the same compute plan.",
            compute_plan_key=compute_plan.key,
        )
        return

    delete_cp_pod_and_dirs_and_optionally_images.apply_async((channel_name, compute_plan.key), queue=worker_queue)


@app.task(ignore_result=False)
def delete_cp_pod_and_dirs_and_optionally_images(channel_name: str, compute_plan_key: str) -> None:
    with get_orchestrator_client(channel_name) as client:
        _teardown_compute_plan_resources(client, compute_plan_key)


def _teardown_compute_plan_resources(orc_client: orchestrator.Client, compute_plan_key: str) -> None:
    structlog.contextvars.bind_contextvars(compute_plan_key=compute_plan_key)

    with acquire_compute_plan_lock(compute_plan_key):
        if orc_client.is_compute_plan_doing(compute_plan_key):
            logger.info("Skipping teardown, compute plan is still running")
            return
        _teardown_pods_and_dirs(compute_plan_key)

    _delete_compute_plan_algos_images(orc_client.query_algos(compute_plan_key))


def _teardown_pods_and_dirs(compute_plan_key: str) -> None:
    release_worker(compute_plan_key)
    delete_compute_plan_pods(compute_plan_key)
    teardown_compute_plan_dir(Directories(compute_plan_key))


def _delete_compute_plan_algos_images(algos: typing.Iterable[orchestrator.Algo]) -> None:
    for algo in algos:
        delete_container_image_safe(utils.container_image_tag_from_algo(algo))

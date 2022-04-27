import structlog
from django.conf import settings

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.computetask_pb2 as computetask_pb2
from backend.celery import app
from substrapp.compute_tasks.algo import Algo
from substrapp.compute_tasks.compute_pod import delete_compute_plan_pods
from substrapp.compute_tasks.directories import Directories
from substrapp.compute_tasks.directories import teardown_compute_plan_dir
from substrapp.compute_tasks.lock import get_compute_plan_lock
from substrapp.docker_registry import delete_container_image_safe
from substrapp.orchestrator import get_orchestrator_client
from substrapp.task_routing import release_worker

logger = structlog.get_logger(__name__)


def queue_delete_cp_pod_and_dirs_and_optionally_images(channel_name, compute_plan):
    compute_plan_key = compute_plan["key"]

    if settings.DEBUG_KEEP_POD_AND_DIRS:
        return

    from substrapp.task_routing import get_existing_worker_queue

    worker_queue = get_existing_worker_queue(compute_plan_key)

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
            compute_plan_key=compute_plan_key,
        )
        return

    delete_cp_pod_and_dirs_and_optionally_images.apply_async((channel_name, compute_plan), queue=worker_queue)


@app.task(ignore_result=False)
def delete_cp_pod_and_dirs_and_optionally_images(channel_name, compute_plan):

    compute_plan_key = compute_plan["key"]
    with get_orchestrator_client(channel_name) as client:
        algos = client.query_algos(
            categories=[
                algo_pb2.AlgoCategory.ALGO_SIMPLE,
                algo_pb2.AlgoCategory.ALGO_COMPOSITE,
                algo_pb2.AlgoCategory.ALGO_AGGREGATE,
            ],
            compute_plan_key=compute_plan_key,
        )
        test_tasks = client.query_tasks(category=computetask_pb2.TASK_TEST, compute_plan_key=compute_plan_key)
    algo_keys = [x["key"] for x in algos]
    metric_keys = [key for task in test_tasks for key in task["test"]["metric_keys"]]

    # See lock function PyDoc for explanation as to why this lock is necessary
    with get_compute_plan_lock(compute_plan_key):

        # Check the CP is still ready for teardown
        with get_orchestrator_client(channel_name) as client:
            is_cp_running = client.is_compute_plan_doing(compute_plan_key)
        if is_cp_running:
            raise Exception(f"Skipping teardown of CP {compute_plan_key}: CP is still running.")

        release_worker(compute_plan_key)
        # Teardown
        delete_compute_plan_pods(compute_plan_key)
        dirs = Directories(compute_plan_key)
        teardown_compute_plan_dir(dirs)

    _remove_docker_images(algo_keys)
    _remove_docker_images(metric_keys)


def _remove_docker_images(keys: list[str]):
    for key in keys:
        image_tag = Algo.image_tag(key)
        delete_container_image_safe(image_tag)

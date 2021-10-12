from __future__ import absolute_import, unicode_literals
import structlog
from django.conf import settings
from backend.celery import app
from substrapp.compute_tasks.context import get_image_tag, METRICS_IMAGE_PREFIX, ALGO_IMAGE_PREFIX
from substrapp.compute_tasks.directories import Directories, teardown_compute_plan_dir
from substrapp.compute_tasks.compute_pod import delete_compute_plan_pods
from substrapp.compute_tasks.lock import get_compute_plan_lock
from substrapp.orchestrator import get_orchestrator_client
import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.docker_registry import delete_container_image
from substrapp.task_routing import release_worker


logger = structlog.get_logger(__name__)


def queue_delete_cp_pod_and_dirs_and_optionally_images(channel_name, compute_plan):
    compute_plan_key = compute_plan["key"]

    if settings.DEBUG_KEEP_POD_AND_DIRS:
        return

    from substrapp.task_routing import get_existing_worker_queue
    worker_queue = get_existing_worker_queue(compute_plan_key)

    if worker_queue is None:
        # the compute plan is not mapped to any worker.
        # so no compute pod should be running.
        logger.warning(
            "Compute plan is finished but no action will be performed to delete the"
            "compute pods and teardown the compute plan dirs because the compute plan"
            "is not mapped to any worker. Here are ideas for investigations: This may"
            "be due to the fact that this compute plan did not have any task ran on"
            "this organisation, or to the fact that the pods and directories were"
            "removed by a parallel process.",
            plan=compute_plan_key,
        )

        return

    delete_cp_pod_and_dirs_and_optionally_images.apply_async((channel_name, compute_plan), queue=worker_queue)


@app.task(ignore_result=False)
def delete_cp_pod_and_dirs_and_optionally_images(channel_name, compute_plan):

    compute_plan_key = compute_plan["key"]
    with get_orchestrator_client(channel_name) as client:
        algos = client.query_algos(compute_plan_key=compute_plan_key)
        test_tasks = client.query_tasks(category=computetask_pb2.TASK_TEST, compute_plan_key=compute_plan_key)
    algo_keys = [x["key"] for x in algos]
    metric_keys = [y for x in test_tasks for y in x["test"]["metric_keys"]]

    # See lock function PyDoc for explanation as to why this lock is necessary
    with get_compute_plan_lock(compute_plan_key):

        # Check the CP is still ready for teardown
        with get_orchestrator_client(channel_name) as client:
            is_cp_running = client.is_compute_plan_doing(compute_plan_key)
        if is_cp_running:
            raise Exception(
                f"Skipping teardown of CP {compute_plan_key}: CP is still running."
            )

        release_worker(compute_plan_key)
        # Teardown
        delete_compute_plan_pods(compute_plan_key)
        dirs = Directories(compute_plan_key)
        teardown_compute_plan_dir(dirs)

    if not settings.DEBUG_QUICK_IMAGE:
        _remove_docker_images(ALGO_IMAGE_PREFIX, algo_keys)
        _remove_docker_images(METRICS_IMAGE_PREFIX, metric_keys)


def _remove_docker_images(image_prefix, keys):
    for key in keys:
        image_tag = get_image_tag(image_prefix, key)
        delete_container_image(image_tag)

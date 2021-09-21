from __future__ import absolute_import, unicode_literals
import logging
from django.conf import settings
from backend.celery import app
from substrapp.compute_tasks.context import get_image_tag, METRICS_IMAGE_PREFIX, ALGO_IMAGE_PREFIX
from substrapp.compute_tasks.directories import Directories, teardown_compute_plan_dir
from substrapp.compute_tasks.compute_pod import delete_compute_plan_pods
from substrapp.compute_tasks.lock import get_compute_plan_lock
from substrapp.orchestrator.api import get_orchestrator_client
import substrapp.orchestrator.computetask_pb2 as computetask_pb2
from substrapp.docker_registry import delete_container_image

logger = logging.getLogger(__name__)


@app.task(ignore_result=False)
def delete_cp_pod_and_dirs_and_optionally_images(channel_name, compute_plan):

    compute_plan_key = compute_plan["key"]
    with get_orchestrator_client(channel_name) as client:
        algos = client.query_algos(compute_plan_key=compute_plan_key)
        test_tasks = client.query_tasks(category=computetask_pb2.TASK_TEST, compute_plan_key=compute_plan_key)
    algo_keys = [x["key"] for x in algos]
    objective_keys = [x["test"]["objective_key"] for x in test_tasks]

    # See lock function PyDoc for explanation as to why this lock is necessary
    with get_compute_plan_lock(compute_plan_key):

        # Check the CP is still ready for teardown
        with get_orchestrator_client(channel_name) as client:
            is_cp_running = client.is_compute_plan_doing(compute_plan_key)
        if is_cp_running:
            raise Exception(
                f"Skipping teardown of CP {compute_plan_key}: CP is still running."
            )

        # Teardown
        delete_compute_plan_pods(compute_plan_key)
        dirs = Directories(compute_plan_key)
        teardown_compute_plan_dir(dirs)

    if not settings.DEBUG_QUICK_IMAGE:
        _remove_docker_images(ALGO_IMAGE_PREFIX, algo_keys)
        _remove_docker_images(METRICS_IMAGE_PREFIX, objective_keys)


def _remove_docker_images(image_prefix, keys):
    for key in keys:
        image_tag = get_image_tag(image_prefix, key)
        delete_container_image(image_tag)

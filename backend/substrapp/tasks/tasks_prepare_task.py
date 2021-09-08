from __future__ import absolute_import, unicode_literals

import json
import logging
from typing import Dict
from django.conf import settings
from celery.result import AsyncResult
from substrapp.tasks.tasks_compute_task import compute_task
from backend.celery import app
from substrapp.utils import (
    get_owner,
)
from substrapp.orchestrator.api import get_orchestrator_client
import substrapp.orchestrator.computetask_pb2 as computetask_pb2
from substrapp.exceptions import TaskNotFoundError

logger = logging.getLogger(__name__)

TUPLE_COMMANDS = {
    computetask_pb2.TASK_TRAIN: 'train',
    computetask_pb2.TASK_TEST: 'predict',
    computetask_pb2.TASK_COMPOSITE: 'train',
    computetask_pb2.TASK_AGGREGATE: 'aggregate',
}


@app.task(ignore_result=True)
def prepare_training_task(channel_name):
    prepare_tasks(channel_name, computetask_pb2.TASK_TRAIN)


@app.task(ignore_result=True)
def prepare_testing_task(channel_name):
    prepare_tasks(channel_name, computetask_pb2.TASK_TEST)


@app.task(ignore_result=True)
def prepare_composite_training_task(channel_name):
    prepare_tasks(channel_name, computetask_pb2.TASK_COMPOSITE)


@app.task(ignore_result=True)
def prepare_aggregate_task(channel_name):
    prepare_tasks(channel_name, computetask_pb2.TASK_AGGREGATE)


def prepare_tasks(channel_name: str, task_category: str) -> None:
    with get_orchestrator_client(channel_name) as client:
        tasks = client.query_tasks(
            worker=get_owner(),
            status=computetask_pb2.STATUS_TODO,
            category=task_category
        )

    for task in tasks:
        tkey = task["key"]
        # Verify that celery task does not already exist
        if AsyncResult(tkey).state == "PENDING":
            prepare_task.apply_async((channel_name, task), task_id=tkey, queue=f"{settings.ORG_NAME}.worker")
        else:
            print(f"[Scheduler ({channel_name})] Compute task ({tkey}) already exists")


@app.task(ignore_result=False)
def prepare_task(channel_name: str, task: Dict) -> None:
    from django_celery_results.models import TaskResult

    worker_queue = f"{settings.ORG_NAME}.worker"
    compute_plan_key = task["compute_plan_key"]

    # Early return if task status is not todo
    # Can happen if we re-process all events (backend-server restart)
    # We need to fetch the task again to get the last
    # version of it in case of processing old events
    try:
        with get_orchestrator_client(channel_name) as client:
            metadata = client.query_task(task["key"])
        if computetask_pb2.ComputeTaskStatus.Value(metadata['status']) != computetask_pb2.STATUS_TODO:
            logger.info(f'Skipping task ({task["category"]} {task["key"]}): '
                        f'Not in "STATUS_TODO" state ({metadata["status"]}).')
            return
    except TaskNotFoundError:
        # use the provided task if the previous call fail
        # It can happen for new task that are not already
        # in the ledger local db
        pass

    flresults = TaskResult.objects.filter(
        task_name="substrapp.tasks.tasks_compute_task",
        result__icontains=f'"compute_plan_key": "{compute_plan_key}"',
    )

    if flresults and flresults.count() > 0:
        worker_queue = json.loads(flresults.first().as_dict()["result"])["worker"]

    with get_orchestrator_client(channel_name) as client:
        logger.info(f"Updating task {task['key']} status to STATUS_DOING")
        client.update_task_status(task["key"], computetask_pb2.TASK_ACTION_DOING, log="")

    compute_task.apply_async((channel_name, task, compute_plan_key), queue=worker_queue)

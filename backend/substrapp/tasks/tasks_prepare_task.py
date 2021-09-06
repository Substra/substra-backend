from __future__ import absolute_import, unicode_literals

import json
import logging
from typing import Dict
from django.conf import settings
from celery.result import AsyncResult
from celery.exceptions import Ignore
from substrapp.tasks.tasks_compute_task import compute_task
from backend.celery import app
from substrapp.utils import (
    get_owner,
)
from substrapp.ledger.api import (
    log_start_tuple,
    query_tuples,
    get_object_from_ledger,
)
from substrapp.ledger.exceptions import LedgerStatusError
from substrapp.exceptions import TaskNotFoundError
from substrapp.compute_tasks.categories import (
    TASK_CATEGORY_TRAINTUPLE,
    TASK_CATEGORY_AGGREGATETUPLE,
    TASK_CATEGORY_COMPOSITETRAINTUPLE,
    TASK_CATEGORY_TESTTUPLE,
)

logger = logging.getLogger(__name__)


@app.task(ignore_result=True)
def prepare_training_task(channel_name):
    prepare_tasks(channel_name, TASK_CATEGORY_TRAINTUPLE)


@app.task(ignore_result=True)
def prepare_testing_task(channel_name):
    prepare_tasks(channel_name, TASK_CATEGORY_TESTTUPLE)


@app.task(ignore_result=True)
def prepare_composite_training_task(channel_name):
    prepare_tasks(channel_name, TASK_CATEGORY_COMPOSITETRAINTUPLE)


@app.task(ignore_result=True)
def prepare_aggregate_task(channel_name):
    prepare_tasks(channel_name, TASK_CATEGORY_AGGREGATETUPLE)


def prepare_tasks(channel_name: str, task_category: str) -> None:
    data_owner = get_owner()
    worker_queue = f"{settings.ORG_NAME}.worker"
    tasks = query_tuples(channel_name, task_category, data_owner)

    for task in tasks:
        tkey = task["key"]
        # Verify that celery task does not already exist
        if AsyncResult(tkey).state == "PENDING":
            prepare_task.apply_async((channel_name, task, task_category), task_id=tkey, queue=worker_queue)
        else:
            print(f"[Scheduler ({channel_name})] Compute task ({tkey}) already exists")


@app.task(ignore_result=False)
def prepare_task(channel_name: str, task: Dict, task_category: str) -> None:
    from django_celery_results.models import TaskResult

    compute_plan_key = None
    worker_queue = f"{settings.ORG_NAME}.worker"
    key = task["key"]

    # Early return if task status is not todo
    # Can happen if we re-process all events (backend-server restart)
    # We need to fetch the task again to get the last
    # version of it in case of processing old events
    try:
        status = _get_task_status(channel_name, task_category, key)
        if status != "todo":
            logger.info(f'Skipping task ({task_category} {key}): Not in "todo" state ({status}).')
            return
    except TaskNotFoundError:
        # use the provided task if the previous call fail
        # It can happen for new task that are not already
        # in the ledger local db
        pass

    if "compute_plan_key" in task and task["compute_plan_key"]:
        compute_plan_key = task["compute_plan_key"]
        flresults = TaskResult.objects.filter(
            task_name="substrapp.tasks.tasks.compute_task",
            result__icontains=f'"compute_plan_key": "{compute_plan_key}"',
        )

        if flresults and flresults.count() > 0:
            worker_queue = json.loads(flresults.first().as_dict()["result"])["worker"]

    try:
        log_start_tuple(channel_name, task_category, key)
    except LedgerStatusError as e:
        # Do not log_fail_tuple in this case, because prepare_task tasks are not unique
        # in case of multiple instances of substra backend running for the same organisation
        # So prepare_task tasks are ignored if it cannot log_start_tuple
        logger.exception(e)
        raise Ignore()

    compute_task.apply_async((channel_name, task_category, task, compute_plan_key), queue=worker_queue)


def _find_training_step_tuple_from_key(channel_name, task_key):
    """Get task category and tuple metadata from task key.

    Applies to traintuple, composite traintuple and aggregatetuple.
    """
    metadata = get_object_from_ledger(channel_name, task_key, "queryModelDetails")
    if metadata.get("aggregatetuple"):
        return TASK_CATEGORY_AGGREGATETUPLE, metadata["aggregatetuple"]
    if metadata.get("composite_traintuple"):
        return TASK_CATEGORY_COMPOSITETRAINTUPLE, metadata["composite_traintuple"]
    if metadata.get("traintuple"):
        return TASK_CATEGORY_TRAINTUPLE, metadata["traintuple"]
    raise TaskNotFoundError(f"Key {task_key}: no task found for training step: model: {metadata}")


def _get_testtuple(channel_name, key):
    return get_object_from_ledger(channel_name, key, "queryTesttuple")


def _get_task_status(channel_name, task_category, key):
    if task_category == TASK_CATEGORY_TESTTUPLE:
        testtuple = _get_testtuple(channel_name, key)
        return testtuple["status"]

    _, metadata = _find_training_step_tuple_from_key(channel_name, key)
    return metadata["status"]

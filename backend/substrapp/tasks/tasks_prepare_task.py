from typing import Dict

import structlog
from celery.exceptions import Ignore
from celery.result import AsyncResult

import orchestrator.computetask_pb2 as computetask_pb2
from backend.celery import app
from orchestrator.error import OrcError
from substrapp.exceptions import TaskNotFoundError
from substrapp.orchestrator import get_orchestrator_client
from substrapp.tasks.tasks_compute_task import compute_task
from substrapp.utils import get_owner

logger = structlog.get_logger(__name__)

TUPLE_COMMANDS = {
    computetask_pb2.TASK_TRAIN: "train",
    computetask_pb2.TASK_TEST: "predict",
    computetask_pb2.TASK_COMPOSITE: "train",
    computetask_pb2.TASK_AGGREGATE: "aggregate",
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
        tasks = client.query_tasks(worker=get_owner(), status=computetask_pb2.STATUS_TODO, category=task_category)

    for task in tasks:
        queue_prepare_task(channel_name, task)


def queue_prepare_task(channel_name, task):
    from substrapp.task_routing import get_worker_queue

    key = task["key"]

    # Verify that celery task does not already exist
    if AsyncResult(key).state != "PENDING":
        logger.info(
            "skipping this task because it already exists",
            task_key=key,
        )
        return

    if _task_not_runnable(channel_name, task["category"], key):
        # Avoid creating celery task if the compute task is not with STATUS_TODO
        return

    # get mapping cp to worker or create a new one
    worker_queue = get_worker_queue(task["compute_plan_key"])
    logger.info(
        f"Assigned CP to worker queue {worker_queue}",
        plan=task["compute_plan_key"],
        worker_queue=worker_queue,
    )
    prepare_task.apply_async((channel_name, task), task_id=key, queue=worker_queue)


@app.task(bind=True, ignore_result=False)
def prepare_task(self, channel_name: str, task: Dict) -> None:
    # Keep execution flow in the current queue
    queue = self.request.delivery_info["routing_key"]
    compute_plan_key = task["compute_plan_key"]

    if _task_not_runnable(channel_name, task["category"], task["key"]):
        # Check that the compute task to process is in STATUS_TODO
        # There can be some time elapsed between the celery task creation and the time the worker pick up the task
        return

    try:
        with get_orchestrator_client(channel_name) as client:
            logger.info("Updating task status to STATUS_DOING", task_key=task["key"])
            client.update_task_status(task["key"], computetask_pb2.TASK_ACTION_DOING, log="")
    except OrcError as rpc_error:
        logger.exception(
            f"failed to update task status to DOING, {rpc_error.details}",
            task_key=task["key"],
        )
        raise Ignore()
    except Exception as e:
        logger.exception(
            f"failed to update task status to DOING, {e}",
            task_key=task["key"],
        )
        raise Ignore()

    compute_task.apply_async((channel_name, task, compute_plan_key), queue=queue)


def _task_not_runnable(channel_name, task_category, task_key):
    # Early return if task status is not todo
    # Can happen if we re-process all events (backend-server restart)
    # We need to fetch the task again to get the last
    # version of it in case of processing old events
    try:
        with get_orchestrator_client(channel_name) as client:
            task = client.query_task(task_key)
    except TaskNotFoundError:
        # use the provided task if the previous call fail
        # It can happen for new task that are not already
        # in the ledger local db
        return False

    if computetask_pb2.ComputeTaskStatus.Value(task["status"]) != computetask_pb2.STATUS_TODO:
        logger.info(
            'Skipping task, not in "STATUS_TODO" state',
            task_key=task_key,
            task_category=task_category,
            status=task["status"],
        )
        return True

    return False

"""
This file contains the main logic for executing a compute task:

- Create execution context
- Populate asset buffer
- Loads assets from the asset buffer
- Build container images
- **Execute the compute task**
- Save the models/results
- Teardown the context

We also handle the retry logic here.
"""

from __future__ import annotations

import errno
import os
from typing import Any
from typing import Optional
from typing import Tuple

import celery.exceptions
import structlog
from billiard.einfo import ExceptionInfo
from celery import Task
from celery.result import AsyncResult
from django.conf import settings
from django.core import files

import orchestrator.computetask_pb2 as computetask_pb2
from backend.celery import app
from substrapp import models
from substrapp import utils
from substrapp.compute_tasks import compute_task as task_utils
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.compute_tasks.asset_buffer import add_assets_to_taskdir
from substrapp.compute_tasks.asset_buffer import add_task_assets_to_buffer
from substrapp.compute_tasks.asset_buffer import clear_assets_buffer
from substrapp.compute_tasks.asset_buffer import init_asset_buffer
from substrapp.compute_tasks.chainkeys import prepare_chainkeys_dir
from substrapp.compute_tasks.compute_pod import delete_compute_plan_pods
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import CPDirName
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.directories import init_compute_plan_dirs
from substrapp.compute_tasks.directories import init_task_dirs
from substrapp.compute_tasks.directories import restore_dir
from substrapp.compute_tasks.directories import teardown_task_dirs
from substrapp.compute_tasks.execute import execute_compute_task
from substrapp.compute_tasks.image_builder import build_image
from substrapp.compute_tasks.lock import MAX_TASK_DURATION
from substrapp.compute_tasks.lock import acquire_compute_plan_lock
from substrapp.compute_tasks.outputs import save_outputs
from substrapp.lock_local import lock_resource
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import get_owner
from substrapp.utils import list_dir

logger = structlog.get_logger(__name__)


class ComputeTask(Task):

    autoretry_for = settings.CELERY_TASK_AUTORETRY_FOR
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    retry_backoff = settings.CELERY_TASK_RETRY_BACKOFF
    retry_backoff_max = settings.CELERY_TASK_RETRY_BACKOFF_MAX
    retry_jitter = settings.CELERY_TASK_RETRY_JITTER

    @property
    def attempt(self) -> int:
        return self.request.retries + 1  # type: ignore

    def on_success(self, retval: dict[str, Any], task_id: str, args: Tuple, kwargs: dict[str, Any]) -> None:
        from django.db import close_old_connections

        close_old_connections()

    def on_retry(self, exc: Exception, task_id: str, args: Tuple, kwargs: dict[str, Any], einfo: ExceptionInfo) -> None:
        _, task = self.split_args(args)
        # delete compute pod to reset hardware ressources
        delete_compute_plan_pods(task["compute_plan_key"])
        logger.info(
            "Retrying task",
            celery_task_id=task_id,
            attempt=(self.attempt + 1),
            max_attempts=(settings.CELERY_TASK_MAX_RETRIES + 1),
        )

    def on_failure(
        self, exc: Exception, task_id: str, args: Tuple, kwargs: dict[str, Any], einfo: ExceptionInfo
    ) -> None:
        from django.db import close_old_connections

        close_old_connections()

        channel_name, task = self.split_args(args)
        compute_task_key = task["key"]

        failure_report = _store_failure(exc, compute_task_key)
        error_type = compute_task_errors.get_error_type(exc)

        with get_orchestrator_client(channel_name) as client:
            # On the backend, only execution errors lead to the creation of compute task failure report instances
            # to store the execution logs.
            if failure_report:
                logs_address = {
                    "checksum": failure_report.logs_checksum,
                    "storage_address": failure_report.logs_address,
                }
            else:
                logs_address = None

            client.register_failure_report(
                {"compute_task_key": compute_task_key, "error_type": error_type, "logs_address": logs_address}
            )

    def split_args(self, celery_args: Tuple) -> Tuple[str, dict[str, Any]]:
        channel_name = celery_args[0]
        task = celery_args[1]
        return channel_name, task


@app.task(ignore_result=True)
def prepare_training_task(channel_name: str) -> None:
    prepare_tasks(channel_name, computetask_pb2.TASK_TRAIN)


@app.task(ignore_result=True)
def prepare_testing_task(channel_name: str) -> None:
    prepare_tasks(channel_name, computetask_pb2.TASK_TEST)


@app.task(ignore_result=True)
def prepare_composite_training_task(channel_name: str) -> None:
    prepare_tasks(channel_name, computetask_pb2.TASK_COMPOSITE)


@app.task(ignore_result=True)
def prepare_aggregate_task(channel_name: str) -> None:
    prepare_tasks(channel_name, computetask_pb2.TASK_AGGREGATE)


def prepare_tasks(channel_name: str, task_category: computetask_pb2.ComputeTaskCategory.V) -> None:
    with get_orchestrator_client(channel_name) as client:
        tasks = client.query_tasks(worker=get_owner(), status=computetask_pb2.STATUS_TODO, category=task_category)

    for task in tasks:
        queue_compute_task(channel_name, task)


def queue_compute_task(channel_name: str, task: dict[str, Any]) -> None:
    from substrapp.task_routing import get_worker_queue

    task_key = task["key"]

    # Verify that celery task does not already exist
    if AsyncResult(task_key).state != "PENDING":
        logger.info(
            "skipping this task because is already exists",
            compute_task_key=task_key,
            celery_task_key=task_key,
        )
        return

    with get_orchestrator_client(channel_name) as client:
        if not task_utils.is_task_runnable(task_key, client):
            return  # avoid creating a Celery task

    # get mapping cp to worker or create a new one
    worker_queue = get_worker_queue(task["compute_plan_key"])
    logger.info(
        "Assigned compute plan to worker queue",
        compute_task_key=task_key,
        compute_plan_key=task["compute_plan_key"],
        worker_queue=worker_queue,
    )

    compute_task.apply_async((channel_name, task, task["compute_plan_key"]), queue=worker_queue, task_id=task_key)


@app.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=False,
    base=ComputeTask,
)
# Ack late and reject on worker lost allows use to
# see http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-reject-on-worker-lost
# and https://github.com/celery/celery/issues/5106
def compute_task(self: ComputeTask, channel_name: str, task: dict[str, Any], compute_plan_key: str) -> None:
    try:
        _run(self, channel_name, task, compute_plan_key)
    except (task_utils.ComputePlanNonRunnableStatusError, task_utils.TaskNonRunnableStatusError) as exception:
        logger.exception(exception)
        raise celery.exceptions.Ignore
    except compute_task_errors.CeleryNoRetryError as exception:
        logger.exception(exception)
        raise
    except compute_task_errors.CeleryRetryError as exception:
        logger.exception(exception)
        raise
    except Exception as exception:
        logger.exception(exception)
        raise compute_task_errors.CeleryRetryError() from exception


# TODO: function too complex, consider refactoring
def _run(self: ComputeTask, channel_name: str, task: dict[str, Any], compute_plan_key: str) -> None:  # noqa: C901
    task_category = computetask_pb2.ComputeTaskCategory.Value(task["category"])
    task_key = task["key"]
    logger.bind(compute_task_key=task_key, compute_plan_key=compute_plan_key, attempt=self.attempt)

    # In case of retries: only execute the compute task if it is not in a final state
    with get_orchestrator_client(channel_name) as client:
        task = client.query_task(task_key)
        # Set allow_doing=True to allow celery retries.
        task_utils.abort_task_if_not_runnable(task_key, client, allow_doing=True, task=task)
        # Try to set the tasks status to DOING if it is not already the case
        task_utils.start_task_if_not_started(task, client)

    logger.info(
        "Computing task",
        task_category=computetask_pb2.ComputeTaskCategory.Name(task_category),
        task=task,
    )
    ctx = None
    dirs = None

    try:
        # Create context
        ctx = Context.from_task(channel_name, task)
        dirs = ctx.directories

        # Setup
        init_asset_buffer()
        init_compute_plan_dirs(dirs)
        init_task_dirs(dirs)

        build_image(ctx.algo)

        with acquire_compute_plan_lock(compute_plan_key):

            # Check the task/cp status again, as the task/cp may not be in a runnable state anymore
            with get_orchestrator_client(channel_name) as client:
                # Set allow_doing=True to allow celery retries.
                task_utils.abort_task_if_not_runnable(task_key, client, allow_doing=True)

            with lock_resource("asset-buffer", "global", timeout=MAX_TASK_DURATION):
                add_task_assets_to_buffer(ctx)

            add_assets_to_taskdir(ctx)

            if task_category != computetask_pb2.TASK_TEST:
                if ctx.has_chainkeys:
                    _prepare_chainkeys(ctx.directories.compute_plan_dir, ctx.compute_plan_tag)
                    restore_dir(dirs, CPDirName.Chainkeys, TaskDirName.Chainkeys)

            restore_dir(dirs, CPDirName.Local, TaskDirName.Local)  # testtuple "predict" may need local dir

            logger.debug("Task directory", directory=list_dir(dirs.task_dir))

            # Command execution
            execute_compute_task(ctx)

            # Collect results
            save_outputs(ctx)
            with get_orchestrator_client(channel_name) as client:
                task_utils.mark_as_done(ctx.task_key, client)

    except OSError as e:
        if e.errno == errno.ENOSPC:
            # "No space left on device"
            # clear asset buffer and retry the task
            logger.info(
                "No space left on device, clearing up the asset buffer and retrying the task", task_key=task["key"]
            )
            with lock_resource("asset-buffer", "", timeout=MAX_TASK_DURATION):
                clear_assets_buffer()
        raise

    finally:
        # Teardown
        try:
            if dirs:
                teardown_task_dirs(dirs)
        except FileNotFoundError:
            # This happens when the CP directory is deleted (because a task failed on another organization)
            # while a task's container images were being built on this organization. Nothing to do.
            pass

    logger.info("Compute task finished")


def _prepare_chainkeys(compute_plan_dir: str, compute_plan_tag: str) -> None:
    chainkeys_dir = os.path.join(compute_plan_dir, CPDirName.Chainkeys)
    prepare_chainkeys_dir(chainkeys_dir, compute_plan_tag)  # does nothing if chainkeys already populated


def _store_failure(exc: Exception, compute_task_key: str) -> Optional[models.ComputeTaskFailureReport]:
    """If the provided exception is an `ExecutionError`, store its logs in the Django storage and in the database.
    Otherwise, do nothing.

    Returns:
        An instance of `models.ComputeTaskFailureReport` storing the data of the `ExecutionError` or None
        if the provided exception is not an `ExecutionError`.
    """

    if not isinstance(exc, compute_task_errors.ExecutionError):
        return None

    file = files.File(exc.logs)
    failure_report = models.ComputeTaskFailureReport(
        compute_task_key=compute_task_key, logs_checksum=utils.get_hash(file)
    )
    failure_report.logs.save(name=compute_task_key, content=file, save=True)
    return failure_report

"""
This file contains the main logic for executing a compute task:

- Create execution context
- Populate asset buffer
- Loads assets from the asset buffer
- **Execute the compute task**
- Save the models/results
- Teardown the context

We also handle the retry logic here.
"""

from __future__ import annotations

import datetime
import enum
import errno
import os
from typing import Any
from typing import Optional

import celery.exceptions
import structlog
from billiard.einfo import ExceptionInfo
from celery import Task
from celery.result import AsyncResult
from django.conf import settings
from django.core import files
from rest_framework import status

import orchestrator
from backend.celery import app
from builder import exceptions as builder_errors
from builder.tasks.tasks_build_image import build_image
from substrapp import models
from substrapp import utils
from substrapp.clients import organization as organization_client
from substrapp.compute_tasks import compute_task as task_utils
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.compute_tasks.asset_buffer import add_assets_to_taskdir
from substrapp.compute_tasks.asset_buffer import add_task_assets_to_buffer
from substrapp.compute_tasks.asset_buffer import clear_assets_buffer
from substrapp.compute_tasks.asset_buffer import init_asset_buffer
from substrapp.compute_tasks.chainkeys import prepare_chainkeys_dir
from substrapp.compute_tasks.compute_pod import delete_compute_plan_pods
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.datastore import Datastore
from substrapp.compute_tasks.datastore import get_datastore
from substrapp.compute_tasks.directories import CPDirName
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.directories import init_compute_plan_dirs
from substrapp.compute_tasks.directories import init_task_dirs
from substrapp.compute_tasks.directories import restore_dir
from substrapp.compute_tasks.directories import teardown_task_dirs
from substrapp.compute_tasks.execute import execute_compute_task
from substrapp.compute_tasks.image_builder import wait_for_image_built
from substrapp.compute_tasks.lock import MAX_TASK_DURATION
from substrapp.compute_tasks.lock import acquire_compute_plan_lock
from substrapp.compute_tasks.outputs import OutputSaver
from substrapp.exceptions import OrganizationHttpError
from substrapp.lock_local import lock_resource
from substrapp.orchestrator import get_orchestrator_client
from substrapp.task_routing import get_builder_queue
from substrapp.utils import Timer
from substrapp.utils import list_dir
from substrapp.utils import retry
from substrapp.utils.url import TASK_PROFILING_BASE_URL
from substrapp.utils.url import get_task_profiling_detail_url
from substrapp.utils.url import get_task_profiling_steps_base_url
from substrapp.utils.url import get_task_profiling_steps_detail_url

logger = structlog.get_logger(__name__)


class ComputeTaskSteps(enum.Enum):
    BUILD_IMAGE = "build_image"
    PREPARE_INPUTS = "prepare_inputs"
    TASK_EXECUTION = "task_execution"
    SAVE_OUTPUTS = "save_outputs"


class ComputeTask(Task):
    autoretry_for = settings.CELERY_TASK_AUTORETRY_FOR
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    retry_backoff = settings.CELERY_TASK_RETRY_BACKOFF
    retry_backoff_max = settings.CELERY_TASK_RETRY_BACKOFF_MAX
    retry_jitter = settings.CELERY_TASK_RETRY_JITTER

    @property
    def attempt(self) -> int:
        return self.request.retries + 1  # type: ignore

    def on_success(self, retval: dict[str, Any], task_id: str, args: tuple, kwargs: dict[str, Any]) -> None:
        from django.db import close_old_connections

        close_old_connections()

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: ExceptionInfo) -> None:
        _, task = self.split_args(args)
        # delete compute pod to reset hardware ressources
        delete_compute_plan_pods(task.compute_plan_key)
        logger.info(
            "Retrying task",
            celery_task_id=task_id,
            attempt=(self.attempt + 1),
            max_attempts=(settings.CELERY_TASK_MAX_RETRIES + 1),
        )

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: ExceptionInfo
    ) -> None:
        from django.db import close_old_connections

        close_old_connections()

        channel_name, task = self.split_args(args)
        compute_task_key = task.key

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

    def split_args(self, celery_args: tuple) -> tuple[str, orchestrator.ComputeTask]:
        channel_name = celery_args[0]
        task = orchestrator.ComputeTask.model_validate_json(celery_args[1])
        return channel_name, task


def queue_compute_task(channel_name: str, task: orchestrator.ComputeTask) -> None:
    from substrapp.task_routing import get_worker_queue

    # Verify that celery task does not already exist
    if AsyncResult(task.key).state != "PENDING":
        logger.info(
            "skipping this task because is already exists",
            compute_task_key=task.key,
            celery_task_key=task.key,
        )
        return

    # add image build to the Celery queue
    with get_orchestrator_client(channel_name) as client:
        function = client.query_function(task.function_key)
    builder_queue = get_builder_queue()

    logger.info(
        "Assigned function to builder queue",
        function_key=function.key,
        compute_task_key=task.key,
        compute_plan_key=task.compute_plan_key,
        queue=builder_queue,
    )
    # TODO switch to function.model_dump_json() as soon as pydantic is updated to > 2.0
    build_image.apply_async((function.json(), channel_name, task.key), queue=builder_queue, task_id=function.key)

    with get_orchestrator_client(channel_name) as client:
        if not task_utils.is_task_runnable(task.key, client):
            return  # avoid creating a Celery task

    # get mapping cp to worker or create a new one
    worker_queue = get_worker_queue(task.compute_plan_key)
    logger.info(
        "Assigned compute plan to worker queue",
        compute_task_key=task.key,
        compute_plan_key=task.compute_plan_key,
        worker_queue=worker_queue,
    )

    compute_task.apply_async((channel_name, task, task.compute_plan_key), queue=worker_queue, task_id=task.key)


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
def compute_task(self: ComputeTask, channel_name: str, serialized_task: str, compute_plan_key: str) -> None:
    task = orchestrator.ComputeTask.model_validate_json(serialized_task)
    datastore = get_datastore(channel=channel_name)
    try:
        _run(self, channel_name, task, compute_plan_key, datastore)
    except (task_utils.ComputePlanNonRunnableError, task_utils.TaskNonRunnableStatusError) as exception:
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


def _send_profiling_event(*, channel_name: str, url_create: str, url_update: str, data: dict[str, Any]) -> bytes:
    try:
        return organization_client.post(channel_name, settings.LEDGER_MSP_ID, url_create, data)
    except OrganizationHttpError as e:
        if e.status_code == status.HTTP_409_CONFLICT:
            return organization_client.put(channel_name, settings.LEDGER_MSP_ID, url_update, data)
        else:
            raise e


@retry()
def _create_task_profiling(channel_name: str, compute_task_key: str) -> bytes:
    url_create = TASK_PROFILING_BASE_URL
    url_update = get_task_profiling_detail_url(compute_task_key)
    data = {"compute_task_key": compute_task_key}
    return _send_profiling_event(channel_name=channel_name, url_create=url_create, url_update=url_update, data=data)


@retry()
def _create_task_profiling_step(
    channel_name: str, compute_task_key: str, field: ComputeTaskSteps, duration: datetime.timedelta
) -> bytes:
    url_create = get_task_profiling_steps_base_url(compute_task_key)
    url_update = get_task_profiling_steps_detail_url(compute_task_key, field.value)
    data = {"step": field.value, "duration": duration}
    return _send_profiling_event(channel_name=channel_name, url_create=url_create, url_update=url_update, data=data)


# TODO: function too complex, consider refactoring
def _run(
    self: ComputeTask, channel_name: str, task: orchestrator.ComputeTask, compute_plan_key: str, datastore: Datastore
) -> None:  # noqa: C901
    timer = Timer()
    _create_task_profiling(channel_name, task.key)

    structlog.contextvars.bind_contextvars(
        compute_task_key=task.key, compute_plan_key=compute_plan_key, attempt=self.attempt
    )

    # In case of retries: only execute the compute task if it is not in a final state
    with get_orchestrator_client(channel_name) as client:
        task = client.query_task(task.key)
        # Set allow_doing=True to allow celery retries.
        task_utils.abort_task_if_not_runnable(task.key, client, allow_doing=True, task=task)
        # Try to set the tasks status to DOING if it is not already the case
        task_utils.start_task_if_not_started(task, client)

    logger.info(
        "Computing task",
        task=task,
    )
    dirs = None

    try:
        # Create context
        ctx = Context.from_task(channel_name, task)
        dirs = ctx.directories

        # Setup
        init_asset_buffer()
        init_compute_plan_dirs(dirs)
        init_task_dirs(dirs)

        # start build_image timer
        timer.start()

        wait_for_image_built(ctx.function)

        # stop build_image timer
        _create_task_profiling_step(channel_name, task.key, ComputeTaskSteps.BUILD_IMAGE, timer.stop())

        with acquire_compute_plan_lock(compute_plan_key):
            # Check the task/cp status again, as the task/cp may not be in a runnable state anymore
            with get_orchestrator_client(channel_name) as client:
                # Set allow_doing=True to allow celery retries.
                task_utils.abort_task_if_not_runnable(task.key, client, allow_doing=True)

            # start inputs loading timer
            timer.start()

            with lock_resource("asset-buffer", "global", timeout=MAX_TASK_DURATION):
                add_task_assets_to_buffer(ctx)

            add_assets_to_taskdir(ctx)

            if ctx.has_chainkeys:
                _prepare_chainkeys(ctx.directories.compute_plan_dir, ctx.compute_plan.tag)
                restore_dir(dirs, CPDirName.Chainkeys, TaskDirName.Chainkeys)

            # stop inputs loading timer
            _create_task_profiling_step(channel_name, task.key, ComputeTaskSteps.PREPARE_INPUTS, timer.stop())

            logger.debug("Task directory", directory=list_dir(dirs.task_dir))

            # start task_execution timer
            timer.start()

            # Command execution
            execute_compute_task(ctx)

            # stop task_execution timer
            _create_task_profiling_step(channel_name, task.key, ComputeTaskSteps.TASK_EXECUTION, timer.stop())

            # start outputs saving timer
            timer.start()

            # Collect results
            saver = OutputSaver(ctx)
            saver.save_outputs()

            # stop outputs saving timer
            _create_task_profiling_step(channel_name, task.key, ComputeTaskSteps.SAVE_OUTPUTS, timer.stop())

            with get_orchestrator_client(channel_name) as client:
                task_utils.mark_as_done(ctx.task.key, client)

    except OSError as e:
        if e.errno == errno.ENOSPC:
            # "No space left on device"
            # clear asset buffer and retry the task
            logger.info(
                "No space left on device, clearing up the asset buffer and retrying the task", task_key=task.key
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
    """If the provided exception is a `BuildError` or an `ExecutionError`, store its logs in the Django storage and
    in the database. Otherwise, do nothing.

    Returns:
        An instance of `models.ComputeTaskFailureReport` storing the error logs or None if the provided exception is
        neither a `BuildError` nor an `ExecutionError`.
    """

    if not isinstance(exc, (compute_task_errors.ExecutionError, builder_errors.BuildError)):
        return None

    file = files.File(exc.logs)
    failure_report = models.ComputeTaskFailureReport(
        compute_task_key=compute_task_key, logs_checksum=utils.get_hash(file)
    )
    failure_report.logs.save(name=compute_task_key, content=file, save=True)
    return failure_report

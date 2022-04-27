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

import errno
import json
import os
from os import path
from typing import Optional

import celery.exceptions
import structlog
from celery import Task
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
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.compute_pod import delete_compute_plan_pods
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import CPDirName
from substrapp.compute_tasks.directories import Directories
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.directories import commit_dir
from substrapp.compute_tasks.directories import init_compute_plan_dirs
from substrapp.compute_tasks.directories import init_task_dirs
from substrapp.compute_tasks.directories import restore_dir
from substrapp.compute_tasks.directories import teardown_task_dirs
from substrapp.compute_tasks.execute import execute_compute_task
from substrapp.compute_tasks.image_builder import build_images
from substrapp.compute_tasks.save_models import save_models
from substrapp.compute_tasks.transfer_bucket import TAG_VALUE_FOR_TRANSFER_BUCKET
from substrapp.compute_tasks.transfer_bucket import transfer_to_bucket
from substrapp.lock_local import lock_resource
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import list_dir

logger = structlog.get_logger(__name__)

MAX_TASK_DURATION = 24 * 60 * 60  # 1 day


class ComputeTask(Task):

    autoretry_for = settings.CELERY_TASK_AUTORETRY_FOR
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    retry_backoff = settings.CELERY_TASK_RETRY_BACKOFF
    retry_backoff_max = settings.CELERY_TASK_RETRY_BACKOFF_MAX
    retry_jitter = settings.CELERY_TASK_RETRY_JITTER

    @property
    def attempt(self):
        return self.request.retries + 1

    def on_success(self, retval, task_id, args, kwargs):
        from django.db import close_old_connections

        close_old_connections()

        channel_name, task = self.split_args(args)
        with get_orchestrator_client(channel_name) as client:
            category = computetask_pb2.ComputeTaskCategory.Value(task["category"])
            if category == computetask_pb2.TASK_TEST:
                for metric_key, perf in retval["result"]["performances"].items():
                    client.register_performance(
                        {"compute_task_key": task["key"], "metric_key": metric_key, "performance_value": float(perf)}
                    )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        _, task = self.split_args(args)
        # delete compute pod to reset hardware ressources
        delete_compute_plan_pods(task["compute_plan_key"])
        logger.info(
            "Retrying task",
            celery_task_id=task_id,
            attempt=(self.request.retries + 2),
            max_attempts=(settings.CELERY_TASK_MAX_RETRIES + 1),
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
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

    def split_args(self, celery_args):
        channel_name = celery_args[0]
        task = celery_args[1]
        return channel_name, task


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
def compute_task(self, channel_name: str, task, compute_plan_key):  # noqa: C901
    try:
        return _run(self, channel_name, task, compute_plan_key)
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
def _run(self, channel_name: str, task, compute_plan_key):  # noqa: C901
    task_category = computetask_pb2.ComputeTaskCategory.Value(task["category"])

    try:
        worker = self.request.hostname.split("@")[1]
        queue = self.request.delivery_info["routing_key"]
    except Exception:
        worker = f"{settings.ORG_NAME}.worker"
        queue = f"{settings.ORG_NAME}"

    result = {"worker": worker, "queue": queue, "compute_plan_key": compute_plan_key}

    # In case of retries: only execute the compute task if it is not in a final state

    task_key = task["key"]
    logger.bind(compute_task_key=task_key, compute_plan_key=compute_plan_key, attempt=self.attempt)

    with get_orchestrator_client(channel_name) as client:
        # Set allow_doing=True to allow celery retries.
        task_utils.abort_task_if_not_runnable(task_key, client, allow_doing=True)

    logger.info(
        "Computing task",
        task_category=computetask_pb2.ComputeTaskCategory.Name(task_category),
        task=task,
    )
    ctx = None
    dirs = None

    # This lock serves multiple purposes:
    #
    # - *Prevent concurrent pod creation*
    #   Ensure concurrent compute tasks don't try to create the same pod at the same time
    #
    # - *Prevent resource starvation*.
    #   Prevent resource starvation: if two compute tasks from the same compute plan ran at the same time, they would
    #   compete for GPU/CPU/memory resources, and potentially fail.
    #
    # - *Adapt to task dir constraints*.
    #   The compute pod contains only one "task directory", which contains the working data for the current compute
    #   task. Running two compute tasks as part of the same compute plan concurrently would mean that the "task
    #   directory" would be used by two consumers. However, the "task directory" is designed to be used by a single
    #   consumer. For instance, out-models are stored in the "task directory": if 2 compute tasks belonging to the
    #   same compute plan run concurrently, one would overwrite the other's out-model.
    #
    # - *Make testtuple predictions available to the evaluation step*
    #   This is related to the previous point. Ensure that the "predict" and "evaluate" steps of a testtuple are run
    #   immediately one after the other. This is necessary because the "evaluate" step needs the pred.json file
    #   computed by the "predict" step. This file is stored in a shared folder (task_dir). Executing another compute
    #   task in between the two steps would result in the shared folder (task_dir) being altered, and `pred.json`
    #   potentially be lost or overwritten. The function `execute_compute_task` takes care of running both the
    #   "predict" and "evaluate" steps of the testtuple.

    with lock_resource("compute-plan", compute_plan_key, ttl=MAX_TASK_DURATION, timeout=MAX_TASK_DURATION):
        try:
            # Create context
            ctx = Context.from_task(channel_name, task)
            dirs = ctx.directories

            # Setup
            init_asset_buffer()
            init_compute_plan_dirs(dirs)
            init_task_dirs(dirs)

            with lock_resource("asset-buffer", "global", timeout=MAX_TASK_DURATION):
                add_task_assets_to_buffer(ctx)
            add_assets_to_taskdir(ctx)
            if task_category != computetask_pb2.TASK_TEST:
                if ctx.has_chainkeys:
                    _prepare_chainkeys(ctx.directories.compute_plan_dir, ctx.compute_plan_tag)
                    restore_dir(dirs, CPDirName.Chainkeys, TaskDirName.Chainkeys)
            restore_dir(dirs, CPDirName.Local, TaskDirName.Local)  # testtuple "predict" may need local dir

            logger.debug("Task directory", directory=list_dir(dirs.task_dir))

            build_images(ctx.all_algos)

            # Command execution
            execute_compute_task(ctx)

            # Collect results
            if task_category == computetask_pb2.TASK_TEST:
                result["result"] = {"performances": {}}
                for metric in ctx.metrics:
                    result["result"]["performances"][metric.key] = _get_perf(dirs, metric.key)

                _transfer_model_to_bucket(ctx)
            else:
                logger.info("Saving models and local folder")
                save_models(ctx)
                commit_dir(dirs, TaskDirName.Local, CPDirName.Local)
                if ctx.has_chainkeys:
                    commit_dir(dirs, TaskDirName.Chainkeys, CPDirName.Chainkeys)
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
            teardown_task_dirs(dirs)

    logger.info("Compute task finished")
    return result


def _get_perf(dirs: Directories, metric_key: str) -> object:
    with open(
        path.join(dirs.task_dir, TaskDirName.Perf, "-".join([metric_key, Filenames.Performance])), "r"
    ) as perf_file:
        return json.load(perf_file)["all"]


def _prepare_chainkeys(compute_plan_dir: str, compute_plan_tag: str):
    chainkeys_dir = os.path.join(compute_plan_dir, CPDirName.Chainkeys)
    prepare_chainkeys_dir(chainkeys_dir, compute_plan_tag)  # does nothing if chainkeys already populated


def _transfer_model_to_bucket(ctx: Context) -> None:
    """Export model to S3 bucket if the task has appropriate tag"""
    if ctx.task["tag"] and TAG_VALUE_FOR_TRANSFER_BUCKET in ctx.task["tag"]:
        logger.info("Task eligible to bucket export")
        transfer_to_bucket(ctx)


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

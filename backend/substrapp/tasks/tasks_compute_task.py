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

from __future__ import absolute_import, unicode_literals

import logging
import json
import os
from os import path
from django.conf import settings
import substrapp.orchestrator.computetask_pb2 as computetask_pb2
from substrapp.orchestrator.api import get_orchestrator_client
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.context import Context
from substrapp.lock_local import lock_resource
from substrapp.utils import list_dir
from substrapp.compute_tasks.directories import (
    Directories,
    CPDirName,
    TaskDirName,
    init_compute_plan_dirs,
    init_task_dirs,
    teardown_task_dirs,
    restore_dir,
    commit_dir,
)
from substrapp.compute_tasks.asset_buffer import (
    init_asset_buffer,
    add_algo_to_buffer,
    add_metrics_to_buffer,
    add_task_assets_to_buffer,
    add_assets_to_taskdir,
)
from substrapp.compute_tasks.chainkeys import prepare_chainkeys_dir
from substrapp.compute_tasks.save_models import save_models
from substrapp.compute_tasks.image_builder import build_images
from substrapp.compute_tasks.execute import execute_compute_task
from substrapp.compute_tasks.exception_handler import compute_error_code
from substrapp.compute_tasks.transfer_bucket import (
    TAG_VALUE_FOR_TRANSFER_BUCKET,
    transfer_to_bucket,
)
from celery import Task
from backend.celery import app


logger = logging.getLogger(__name__)

CELERY_TASK_MAX_RETRIES = int(getattr(settings, "CELERY_TASK_MAX_RETRIES"))
CELERY_TASK_RETRY_DELAY_SECONDS = int(getattr(settings, "CELERY_TASK_RETRY_DELAY_SECONDS"))

MAX_TASK_DURATION = 24 * 60 * 60  # 1 day


class ComputeTask(Task):
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
                client.register_performance({'compute_task_key': task["key"],
                                             'performance_value': float(retval['result']['global_perf'])})

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.info(f"Retrying task {task_id} (attempt {self.request.retries + 2}/{CELERY_TASK_MAX_RETRIES + 1})")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from django.db import close_old_connections

        close_old_connections()
        channel_name, task = self.split_args(args)

        error_code = compute_error_code(exc)
        # Do not show traceback if it's a container error as we already see them in
        # container log
        type_exc = type(exc)
        type_value = str(type_exc).split("'")[1]
        logger.error(f'Failed compute task: {task["category"]} {task["key"]} {error_code} - {type_value}')
        with get_orchestrator_client(channel_name) as client:
            client.update_task_status(task["key"], computetask_pb2.TASK_ACTION_FAILED, log=error_code)

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
def compute_task(self, channel_name: str, task, compute_plan_key):
    task_category = computetask_pb2.ComputeTaskCategory.Value(task['category'])

    try:
        worker = self.request.hostname.split("@")[1]
        queue = self.request.delivery_info["routing_key"]
    except Exception:
        worker = f"{settings.ORG_NAME}.worker"
        queue = f"{settings.ORG_NAME}"

    result = {"worker": worker, "queue": queue, "compute_plan_key": compute_plan_key}

    # In case of retries: only execute the compute task if it is not in a final state

    task_key = task["key"]

    with get_orchestrator_client(channel_name) as client:
        should_not_run = client.is_task_in_final_state(task_key)
    if should_not_run:
        raise Exception(
            f"Gracefully aborting execution of task {task_key}. Task is not in a runnable state anymore."
        )

    logger.warning(f"{computetask_pb2.ComputeTaskCategory.Name(task_category)} {task_key} {task}")
    ctx = None
    dirs = None
    has_chainkeys = False

    # This lock serves multiple purposes:
    #
    # - *Prevent concurrent pod creation*
    #   Ensure concurrent compute tasks don't try to create the same pod at the same time
    #
    # - *Prevent resource starvation*.
    #   Prevent resource starvation: if two compute tasks from the same compute plan ran at the same time, they would
    #   compete for GPU/CPU/memory resources, and potentially fail.
    #
    # - *Adapt to task dir contraints*.
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
            ctx = Context.from_task(channel_name, task, self.attempt)
            dirs = ctx.directories
            has_chainkeys = settings.TASK["CHAINKEYS_ENABLED"] and ctx.compute_plan_tag

            # Setup
            init_asset_buffer()
            init_compute_plan_dirs(dirs)
            init_task_dirs(dirs)
            add_algo_to_buffer(ctx)
            if ctx.task_category == computetask_pb2.TASK_TEST:
                add_metrics_to_buffer(ctx)
            add_task_assets_to_buffer(ctx)
            add_assets_to_taskdir(ctx)
            if task_category != computetask_pb2.TASK_TEST:
                if has_chainkeys:
                    _prepare_chainkeys(ctx.directories.compute_plan_dir, ctx.compute_plan_tag)
                    restore_dir(dirs, CPDirName.Chainkeys, TaskDirName.Chainkeys)
            restore_dir(dirs, CPDirName.Local, TaskDirName.Local)   # testtuple "predict" may need local dir

            logger.debug(f"Task directory: {list_dir(dirs.task_dir)}")

            build_images(ctx)

            # Command execution
            execute_compute_task(ctx)

            # Collect results
            if task_category == computetask_pb2.TASK_TEST:
                result["result"] = _get_perf(dirs)
                _transfer_model_to_bucket(ctx)
            else:
                result["result"] = save_models(ctx)
                commit_dir(dirs, TaskDirName.Local, CPDirName.Local)
                if has_chainkeys:
                    commit_dir(dirs, TaskDirName.Chainkeys, CPDirName.Chainkeys)

        except Exception as e:
            raise self.retry(
                exc=e,
                countdown=CELERY_TASK_RETRY_DELAY_SECONDS,
                max_retries=CELERY_TASK_MAX_RETRIES,
            )

        finally:
            # Teardown
            teardown_task_dirs(dirs)

    logger.warning(f"result: {result['result']}")
    return result


def _get_perf(dirs: Directories) -> object:
    with open(path.join(dirs.task_dir, TaskDirName.Perf, Filenames.Performance), "r") as perf_file:
        return {"global_perf": json.load(perf_file)["all"]}


def _prepare_chainkeys(compute_plan_dir: str, compute_plan_tag: str):
    chainkeys_dir = os.path.join(compute_plan_dir, CPDirName.Chainkeys)
    prepare_chainkeys_dir(chainkeys_dir, compute_plan_tag)  # does nothing if chainkeys already populated


def _transfer_model_to_bucket(ctx: Context) -> None:
    """Export model to S3 bucket if the task has appropriate tag"""
    if ctx.task_tag and TAG_VALUE_FOR_TRANSFER_BUCKET in ctx.task["tag"]:
        logger.info("Task eligible to bucket export")
        transfer_to_bucket(ctx)

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
from substrapp.compute_tasks.categories import TASK_CATEGORY_TESTTUPLE
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import (
    Directories,
    CPDirName,
    TaskDirName,
    init_compute_plan_dirs,
    init_task_dirs,
    teardown_task_dirs,
    teardown_compute_plan_dir,
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
from substrapp.ledger.exceptions import LedgerError
from substrapp.docker_registry import delete_container_image
from substrapp.lock_local import lock_resource
from celery import Task
from backend.celery import app
from substrapp.ledger.api import log_success_tuple, log_fail_tuple, is_task_runnable


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

        channel_name, task_category, task = self.split_args(args)
        try:
            log_success_tuple(channel_name, task_category, task["key"], retval["result"])
        except LedgerError as e:
            logger.exception(e)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.info(f"Retrying task {task_id} (attempt {self.request.retries + 2}/{CELERY_TASK_MAX_RETRIES + 1})")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from django.db import close_old_connections

        close_old_connections()
        channel_name, task_category, task = self.split_args(args)

        try:
            error_code = compute_error_code(exc)
            # Do not show traceback if it's a container error as we already see them in
            # container log
            type_exc = type(exc)
            type_value = str(type_exc).split("'")[1]
            logger.error(f'Failed compute task: {task_category} {task["key"]} {error_code} - {type_value}')
            log_fail_tuple(channel_name, task_category, task["key"], error_code)
        except LedgerError as e:
            logger.exception(e)

    def split_args(self, celery_args):
        channel_name = celery_args[0]
        task_category = celery_args[1]
        task = celery_args[2]
        return channel_name, task_category, task


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
def compute_task(self, channel_name: str, task_category: str, task, compute_plan_key):
    try:
        worker = self.request.hostname.split("@")[1]
        queue = self.request.delivery_info["routing_key"]
    except Exception:
        worker = f"{settings.ORG_NAME}.worker"
        queue = f"{settings.ORG_NAME}"

    result = {"worker": worker, "queue": queue, "compute_plan_key": compute_plan_key}

    # In case of retries: only execute the compute task if the compute plan hasn't been cancelled
    should_run = is_task_runnable(channel_name, task["key"], task_category, task["compute_plan_key"])
    if not should_run:
        raise Exception(
            f"Gracefully aborting execution of task {task['key']}. Task is not in a runnable state anymore."
        )

    task_key = task["key"]
    logger.warning(f"{task_category} {task_key} {task}")

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
            ctx = Context.from_task(channel_name, task, task_category, self.attempt)
            dirs = ctx.directories
            has_chainkeys = settings.TASK["CHAINKEYS_ENABLED"] and ctx.compute_plan_tag

            # Setup
            init_asset_buffer()
            init_compute_plan_dirs(dirs)
            init_task_dirs(dirs)
            add_algo_to_buffer(ctx)
            if ctx.task_category == TASK_CATEGORY_TESTTUPLE:
                add_metrics_to_buffer(ctx)
            add_task_assets_to_buffer(ctx)
            add_assets_to_taskdir(ctx)
            if task_category != TASK_CATEGORY_TESTTUPLE:
                if has_chainkeys:
                    _prepare_chainkeys(ctx.directories.compute_plan_dir, ctx.compute_plan_tag)
                    restore_dir(dirs, CPDirName.Chainkeys, TaskDirName.Chainkeys)
            restore_dir(dirs, CPDirName.Local, TaskDirName.Local)  # testtuple "predict" may need local dir
            build_images(ctx)

            # Command execution
            execute_compute_task(ctx)

            # Collect results
            if task_category == TASK_CATEGORY_TESTTUPLE:
                result["result"] = _get_perf(dirs)
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
            if not settings.DEBUG_KEEP_POD_AND_DIRS:
                teardown_task_dirs(dirs)

                # TODO orchestrator: delete this block
                if not ctx.compute_plan_key:
                    teardown_compute_plan_dir(dirs)

            # TODO orchestrator: delete this block
            if (
                ctx.compute_plan_key is None and
                not settings.TASK["CACHE_DOCKER_IMAGES"] and
                not settings.DEBUG_QUICK_IMAGE
            ):
                image_tag = ctx.metrics_image_tag if task_category == TASK_CATEGORY_TESTTUPLE else ctx.algo_image_tag
                delete_container_image(image_tag)

    logger.warning(f"result: {result['result']}")
    return result


def _get_perf(dirs: Directories) -> object:
    with open(path.join(dirs.task_dir, TaskDirName.Perf, Filenames.Performance), "r") as perf_file:
        return {"global_perf": json.load(perf_file)["all"]}


def _prepare_chainkeys(compute_plan_dir: str, compute_plan_tag: str):
    chainkeys_dir = os.path.join(compute_plan_dir, CPDirName.Chainkeys)
    prepare_chainkeys_dir(chainkeys_dir, compute_plan_tag)  # does nothing if chainkeys already populated

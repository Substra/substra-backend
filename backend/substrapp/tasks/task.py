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
import enum
import pickle  # nosec B403
from typing import Any

import structlog
from billiard.einfo import ExceptionInfo
from celery import Task
from django.conf import settings

import orchestrator
from substrapp.compute_tasks.compute_pod import delete_compute_plan_pods
from substrapp.models import FailedAssetKind
from substrapp.task_routing import WORKER_QUEUE
from substrapp.tasks.tasks_asset_failure_report import store_asset_failure_report

logger = structlog.get_logger(__name__)


class FailableTask(Task):
    asset_type: FailedAssetKind

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: ExceptionInfo
    ) -> None:
        asset_key, channel_name = self.get_task_info(args, kwargs)
        exception_pickled = pickle.dumps(exc)
        store_asset_failure_report.apply_async(
            args,
            {
                "asset_key": asset_key,
                "asset_type": self.asset_type,
                "channel_name": channel_name,
                "exception_pickled": exception_pickled,
            },
            queue=WORKER_QUEUE,
        )

    def get_task_info(self, args: tuple, kwargs: dict) -> tuple[str, str]:
        raise NotImplementedError()


class ComputeTaskSteps(enum.Enum):
    BUILD_IMAGE = "build_image"
    PREPARE_INPUTS = "prepare_inputs"
    TASK_EXECUTION = "task_execution"
    SAVE_OUTPUTS = "save_outputs"


class ComputeTask(FailableTask):
    autoretry_for = settings.CELERY_TASK_AUTORETRY_FOR
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    retry_backoff = settings.CELERY_TASK_RETRY_BACKOFF
    retry_backoff_max = settings.CELERY_TASK_RETRY_BACKOFF_MAX
    retry_jitter = settings.CELERY_TASK_RETRY_JITTER

    asset_type = FailedAssetKind.FAILED_ASSET_COMPUTE_TASK

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

    def split_args(self, celery_args: tuple) -> tuple[str, orchestrator.ComputeTask]:
        channel_name = celery_args[0]
        task = orchestrator.ComputeTask.parse_raw(celery_args[1])
        return channel_name, task

    def get_task_info(self, args: tuple, kwargs: dict) -> tuple[str, str]:
        channel_name, task = self.split_args(args)

        return task.key, channel_name

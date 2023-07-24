from typing import Any

import structlog
from billiard.einfo import ExceptionInfo
from celery import Task
from django.conf import settings

import orchestrator
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils.errors import store_failure

logger = structlog.get_logger(__name__)


class BuildTask(Task):
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
        logger.info(
            "Retrying build",
            celery_task_id=task_id,
            attempt=(self.attempt + 1),
            max_attempts=(self.max_retries + 1),
        )

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: ExceptionInfo
    ) -> None:
        from django.db import close_old_connections

        close_old_connections()

        channel_name, function, compute_task_key = self.split_args(args)

        failure_report = store_failure(exc, compute_task_key)
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

    def split_args(self, celery_args: tuple) -> tuple[str, orchestrator.Function, str]:
        channel_name = celery_args[1]
        compute_task_key = celery_args[2]
        function = orchestrator.Function.parse_raw(celery_args[0])
        return channel_name, function, compute_task_key

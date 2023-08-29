from typing import Any

import structlog
from billiard.einfo import ExceptionInfo
from celery import Task
from django.conf import settings

import orchestrator

# from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.orchestrator import get_orchestrator_client

# from substrapp.utils.errors import store_failure


logger = structlog.get_logger("builder")


class BuildTask(Task):
    autoretry_for = settings.CELERY_TASK_AUTORETRY_FOR
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    retry_backoff = settings.CELERY_TASK_RETRY_BACKOFF
    retry_backoff_max = settings.CELERY_TASK_RETRY_BACKOFF_MAX
    retry_jitter = settings.CELERY_TASK_RETRY_JITTER
    acks_late = True
    reject_on_worker_lost = True
    ignore_result = False

    @property
    def attempt(self) -> int:
        return self.request.retries + 1  # type: ignore

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: ExceptionInfo
    ) -> None:
        logger.error(exc)
        logger.error(einfo)
        function_key, channel_name = self.get_task_info(args, kwargs)
        with get_orchestrator_client(channel_name) as client:
            client.update_function_status(
                function_key=function_key, action=orchestrator.function_pb2.FUNCTION_ACTION_FAILED
            )

    #  def on_failure(
    #     self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: ExceptionInfo
    # ) -> None:
    # super():on_failure(exc, task_id, args, kwargs, einfo)
    # channel_name, function, compute_task_key = self.split_args(args)

    # failure_report = store_failure(exc, compute_task_key)
    # error_type = compute_task_errors.get_error_type(exc)

    # with get_orchestrator_client(channel_name) as client:
    #     # On the backend, only execution errors lead to the creation of compute task failure report instances
    #     # to store the execution logs.
    #     if failure_report:
    #         logs_address = {
    #             "checksum": failure_report.logs_checksum,
    #             "storage_address": failure_report.logs_address,
    #         }
    #     else:
    #         logs_address = None

    #     client.register_failure_report(
    #         {"compute_task_key": compute_task_key, "error_type": error_type, "logs_address": logs_address}
    #     )

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        function_key, channel_name = self.get_task_info(args, kwargs)
        with get_orchestrator_client(channel_name) as client:
            client.update_function_status(
                function_key=function_key, action=orchestrator.function_pb2.FUNCTION_ACTION_BUILDING
            )

    def get_task_info(self, args: tuple, kwargs: dict) -> tuple[str, str]:
        function = orchestrator.Function.parse_raw(kwargs["function_serialized"])
        channel_name = kwargs["channel_name"]
        return function.key, channel_name

import structlog
from django.conf import settings

import orchestrator
from substrapp.models import FailedAssetKind
from substrapp.orchestrator import get_orchestrator_client
from substrapp.tasks.task import FailableTask

logger = structlog.get_logger("builder")


class BuildTask(FailableTask):
    autoretry_for = settings.CELERY_TASK_AUTORETRY_FOR
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    retry_backoff = settings.CELERY_TASK_RETRY_BACKOFF
    retry_backoff_max = settings.CELERY_TASK_RETRY_BACKOFF_MAX
    retry_jitter = settings.CELERY_TASK_RETRY_JITTER
    acks_late = True
    reject_on_worker_lost = True
    ignore_result = False

    asset_type = FailedAssetKind.FAILED_ASSET_FUNCTION

    @property
    def attempt(self) -> int:
        return self.request.retries + 1  # type: ignore

    # Celery does not provide unpacked arguments, we are doing it in `get_task_info`
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

import pickle  # nosec B403 - internal to the worker

import structlog
from celery import Task
from django.conf import settings

from backend.celery import app
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.models import FailedAssetKind
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils.errors import store_failure

REGISTRY = settings.REGISTRY
REGISTRY_SCHEME = settings.REGISTRY_SCHEME
SUBTUPLE_TMP_DIR = settings.SUBTUPLE_TMP_DIR

logger = structlog.get_logger("worker")


class StoreAssetFailureReportTask(Task):
    max_retries = 0
    reject_on_worker_lost = True
    ignore_result = False

    @property
    def attempt(self) -> int:
        return self.request.retries + 1  # type: ignore

    def get_task_info(self, args: tuple, kwargs: dict) -> tuple[str, str, str]:
        asset_key = kwargs["asset_key"]
        asset_type = kwargs["asset_type"]
        channel_name = kwargs["channel_name"]
        return asset_key, asset_type, channel_name


@app.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=False,
    base=StoreAssetFailureReportTask,
)
def store_asset_failure_report(task, *args, **kwargs) -> None:
    asset_key, asset_type, channel_name = task.get_task_info(args, kwargs)
    exception = pickle.loads(kwargs["exception_pickled"])  # nosec B301

    if asset_type == FailedAssetKind.FAILED_ASSET_FUNCTION:
        error_type = compute_task_errors.ComputeTaskErrorType.BUILD_ERROR.value
    else:
        error_type = compute_task_errors.get_error_type(exception)

    failure_report = store_failure(exception, asset_key, asset_type, error_type)

    with get_orchestrator_client(channel_name) as client:
        # On the backend, only building and execution errors lead to the creation of compute task failure
        # report instances to store the execution logs.
        if failure_report:
            logs_address = {
                "checksum": failure_report.logs_checksum,
                "storage_address": failure_report.logs_address,
            }
        else:
            logs_address = None

        client.register_failure_report(
            {"asset_key": asset_key, "error_type": error_type, "asset_type": asset_type, "logs_address": logs_address}
        )

import pickle  # nosec B403 - internal to the worker

import structlog
from celery import Task
from django.conf import settings

from backend.celery import app
from orchestrator import failure_report_pb2
from orchestrator import get_orchestrator_client
from substrapp.compute_tasks import errors as compute_task_errors
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
def store_asset_failure_report(
    task: StoreAssetFailureReportTask, *, asset_key: str, asset_type: str, channel_name: str, exception_pickled: bytes
) -> None:
    exception = pickle.loads(exception_pickled)  # nosec B301

    error_type = get_error_type(exception)

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


def get_error_type(exc: Exception) -> failure_report_pb2.ErrorType.ValueType:
    """From a given exception, return an error type safe to store and to advertise to the user.

    Args:
        exc: The exception to process.

    Returns:
        The error type corresponding to the exception.
    """

    if not hasattr(exc, "logs"):
        return compute_task_errors.ComputeTaskErrorType.INTERNAL_ERROR.value

    try:
        error_type = exc.error_type
    except AttributeError:
        error_type = compute_task_errors.ComputeTaskErrorType.INTERNAL_ERROR

    return error_type.value

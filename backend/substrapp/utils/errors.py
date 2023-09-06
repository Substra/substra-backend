from typing import Optional

from django.core import files

from orchestrator import failure_report_pb2
from substrapp import models
from substrapp import utils


def store_failure(
    exception, asset_key: str, asset_type: models.FailedAssetKind, error_type: failure_report_pb2.ErrorType
) -> Optional[models.AssetFailureReport]:
    """If the provided exception is a `BuildError` or an `ExecutionError`, store its logs in the Django storage and
    in the database. Otherwise, do nothing.

    Returns:
        An instance of `models.AssetFailureReport` storing the error logs or None if the provided exception is
        neither a `BuildError` nor an `ExecutionError`.
    """

    if error_type not in [failure_report_pb2.ERROR_TYPE_BUILD, failure_report_pb2.ERROR_TYPE_EXECUTION]:
        return None

    file = files.File(exception.logs)
    failure_report = models.AssetFailureReport(
        asset_key=asset_key, asset_type=asset_type, logs_checksum=utils.get_hash(file)
    )
    failure_report.logs.save(name=asset_key, content=file, save=True)
    return failure_report

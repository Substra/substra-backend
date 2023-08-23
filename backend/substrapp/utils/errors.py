from typing import Optional

from django.core import files

from builder import exceptions as builder_errors
from substrapp import models
from substrapp import utils
from substrapp.compute_tasks import errors as compute_task_errors


def store_failure(exc: Exception, asset_key: str, asset_type: str) -> Optional[models.CeleryTaskFailureReport]:
    """If the provided exception is a `BuildError` or an `ExecutionError`, store its logs in the Django storage and
    in the database. Otherwise, do nothing.

    Returns:
        An instance of `models.CeleryTaskFailureReport` storing the error logs or None if the provided exception is
        neither a `BuildError` nor an `ExecutionError`.
    """

    if not isinstance(exc, (compute_task_errors.ExecutionError, builder_errors.BuildError)):
        return None

    file = files.File(exc.logs)
    failure_report = models.CeleryTaskFailureReport(
        asset_key=asset_key, asset_type=asset_type, logs_checksum=utils.get_hash(file)
    )
    failure_report.logs.save(name=asset_key, content=file, save=True)
    return failure_report

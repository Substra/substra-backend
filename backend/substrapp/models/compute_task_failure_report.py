import urllib.parse
from typing import Final

from django.conf import settings
from django.db import models

_UUID_STRING_REPR_LENGTH: Final[int] = 36
_SHA256_STRING_REPR_LENGTH: Final[int] = 256 // 4


def _upload_to(instance: "ComputeTaskFailureReport", _filename: str) -> str:
    return instance.compute_task_key


class ComputeTaskFailureReport(models.Model):
    """Store information relative to a compute task failure."""

    compute_task_key = models.UUIDField(primary_key=True, editable=False)
    logs = models.FileField(
        storage=settings.COMPUTE_TASK_LOGS_STORAGE, max_length=_UUID_STRING_REPR_LENGTH, upload_to=_upload_to
    )
    logs_checksum = models.CharField(max_length=_SHA256_STRING_REPR_LENGTH)
    creation_date = models.DateTimeField(auto_now_add=True)

    @property
    def logs_address(self) -> str:
        logs_path = f"logs/{self.compute_task_key}"
        return urllib.parse.urljoin(settings.DEFAULT_DOMAIN, logs_path)

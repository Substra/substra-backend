import uuid
from typing import Final

from django.conf import settings
from django.db import models

from api.models.utils import URLValidatorWithOptionalTLD
from orchestrator import failure_report_pb2

LOGS_BASE_PATH: Final[str] = "logs"
LOGS_FILE_PATH: Final[str] = "file"

_UUID_STRING_REPR_LENGTH: Final[int] = 36
_SHA256_STRING_REPR_LENGTH: Final[int] = 256 // 4


def _upload_to(instance: "AssetFailureReport", _filename: str) -> str:
    return str(instance.asset_key)


FailedAssetKind = models.TextChoices(
    "FailedAssetKind", [(status_name, status_name) for status_name in failure_report_pb2.FailedAssetKind.keys()]
)


class AssetFailureReport(models.Model):
    """Store information relative to a failure (compute task or function)."""

    asset_key = models.UUIDField(primary_key=True, editable=False)
    asset_type = models.CharField(max_length=100, choices=FailedAssetKind.choices)
    logs = models.FileField(
        storage=settings.ASSET_LOGS_STORAGE, max_length=_UUID_STRING_REPR_LENGTH, upload_to=_upload_to, null=True
    )
    logs_checksum = models.CharField(max_length=_SHA256_STRING_REPR_LENGTH)
    logs_address = models.URLField(validators=[URLValidatorWithOptionalTLD()])
    logs_owner = models.CharField(max_length=100)
    creation_date = models.DateTimeField(auto_now_add=True)

    key_identifier = "asset_key"

    @property
    def key(self) -> uuid.UUID:
        return self.asset_key

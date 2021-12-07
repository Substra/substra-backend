import uuid

from django.conf import settings
from django.db import models

from libs.timestamp_model import TimeStamped
from substrapp.utils import get_hash


def upload_to(instance, filename) -> str:
    return f"metrics/{instance.key}/{filename}"


class Metric(TimeStamped):
    """Storage Metric table"""

    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    validated = models.BooleanField(default=False, blank=True)
    description = models.FileField(
        storage=settings.METRICS_STORAGE, max_length=500, upload_to=upload_to, blank=True, null=True
    )  # path max length to 500 instead of default 100
    address = models.FileField(
        storage=settings.METRICS_STORAGE, max_length=500, upload_to=upload_to, blank=True, null=True
    )
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        """Use hash of description file as checksum"""
        if not self.checksum and self.description:
            self.checksum = get_hash(self.description)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Metric with key {self.key} with validated {self.validated}"

import uuid

from django.conf import settings
from django.db import models

from substrapp.utils import get_hash


def upload_to(instance, filename):
    return f"datamanagers/{instance.key}/{filename}"


class DataManager(models.Model):
    """Storage DataManager table"""

    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=True, max_length=100)
    data_opener = models.FileField(
        storage=settings.DATAMANAGER_STORAGE, max_length=500, upload_to=upload_to
    )  # path max length to 500 instead of default 100
    description = models.FileField(
        storage=settings.DATAMANAGER_STORAGE, max_length=500, upload_to=upload_to
    )  # path max length to 500 instead of default 100
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs) -> None:
        """Use hash of description file as checksum"""
        if not self.checksum and self.data_opener:
            self.checksum = get_hash(self.data_opener)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"DataManager with key {self.key}"

import uuid

from django.conf import settings
from django.db import models

from substrapp.utils import get_hash


def upload_to(instance, filename) -> str:
    return f"models/{instance.key}/{filename}"


class Model(models.Model):
    """Storage Data table"""

    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(
        storage=settings.MODEL_STORAGE,
        upload_to=upload_to,
        max_length=500,
    )  # path max length to 500 instead of default 100
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs) -> None:
        """Use hash of file as checksum"""
        if not self.checksum and self.file:
            self.checksum = get_hash(self.file)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Model with key {self.key}"

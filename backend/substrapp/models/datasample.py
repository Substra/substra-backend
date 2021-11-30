import uuid

from django.conf import settings
from django.db import models


def upload_to(instance, filename):
    return str(instance.key)


class DataSample(models.Model):
    """Storage Data table"""

    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    validated = models.BooleanField(default=False)
    checksum = models.CharField(max_length=64)

    file = models.FileField(
        storage=settings.DATASAMPLE_STORAGE, max_length=500, upload_to=upload_to, blank=True, null=True
    )
    # servermedias use path instead of file
    path = models.FilePathField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"DataSample with key {self.key} with validated {self.validated}"

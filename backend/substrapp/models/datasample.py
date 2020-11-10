from django.db import models
from substrapp.utils import get_hash
import uuid


class DataSample(models.Model):
    """Storage Data table"""
    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    validated = models.BooleanField(default=False)
    path = models.FilePathField(max_length=500,  # path max length to 500 instead of default 100
                                blank=True,
                                null=True)
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        if not self.checksum and self.path:
            self.checksum = get_hash(self.path)
        super(DataSample, self).save(*args, **kwargs)

    def __str__(self):
        return f'DataSample with key {self.key} with validated {self.validated}'

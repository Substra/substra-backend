import uuid
from django.db import models

from libs.timestamp_model import TimeStamped
from substrapp.utils import get_hash


def upload_to(instance, filename):
    return 'metrics/{0}/{1}'.format(instance.key, filename)


class Metric(TimeStamped):
    """Storage Metric table"""
    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    validated = models.BooleanField(default=False, blank=True)
    description = models.FileField(upload_to=upload_to, max_length=500, blank=True, null=True)
    address = models.FileField(upload_to=upload_to, max_length=500, blank=True, null=True)
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        """Use hash of description file as checksum"""
        if not self.checksum and self.description:
            self.checksum = get_hash(self.description)
        super(Metric, self).save(*args, **kwargs)

    def __str__(self):
        return f"Metric with key {self.key} with validated {self.validated}"

import uuid
from django.db import models

from libs.timestamp_model import TimeStamped
from substrapp.utils import get_hash

from substrapp.minio.connection import get_minio_client
from substrapp.minio.djangostorage import MinioStorage


def upload_to(instance, filename):
    return 'objectives/{0}/{1}'.format(instance.key, filename)


class Objective(TimeStamped):
    """Storage Objective table"""
    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    validated = models.BooleanField(default=False, blank=True)
    description = models.FileField(upload_to=upload_to,
                                   storage=MinioStorage(get_minio_client, bucket_name='my-test-bucket'),
                                   max_length=500,
                                   blank=True,
                                   null=True)
    metrics = models.FileField(upload_to=upload_to, max_length=500, blank=True, null=True)
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        """Use hash of description file as checksum"""
        if not self.checksum and self.description:
            self.checksum = get_hash(self.description)
        super(Objective, self).save(*args, **kwargs)

    def __str__(self):
        return f"Objective with key {self.key} with validated {self.validated}"

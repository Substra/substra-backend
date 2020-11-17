from django.db import models
import uuid
from substrapp.utils import get_hash
from substrapp.minio.connection import get_minio_client
from substrapp.minio.djangostorage import MinioStorage


def upload_to(instance, filename):
    return 'models/{0}/{1}'.format(instance.key, filename)


class Model(models.Model):
    """Storage Data table"""
    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    validated = models.BooleanField(default=False)
    file = models.FileField(upload_to=upload_to,
                            storage=MinioStorage(get_minio_client, bucket_name='my-test-bucket'),
                            max_length=500)
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        """Use hash of file as checksum"""
        if not self.checksum and self.file:
            self.checksum = get_hash(self.file)
        super(Model, self).save(*args, **kwargs)

    def __str__(self):
        return f'Model with key {self.key} with validated {self.validated}'

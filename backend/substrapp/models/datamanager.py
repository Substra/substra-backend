from django.db import models
import uuid
from substrapp.utils import get_hash


def upload_to(instance, filename):
    return 'datamanagers/{0}/{1}'.format(instance.pk, filename)


class DataManager(models.Model):
    """Storage DataManager table"""
    pkhash = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=True, max_length=100)
    data_opener = models.FileField(upload_to=upload_to, max_length=500)  # path max length to 500 instead of default 100
    description = models.FileField(upload_to=upload_to, max_length=500)  # path max length to 500 instead of default 100
    validated = models.BooleanField(default=False, blank=True)
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        """Use hash of description file as checksum"""
        if not self.checksum and self.data_opener:
            self.checksum = get_hash(self.data_opener)
        super(DataManager, self).save(*args, **kwargs)

    def __str__(self):
        return f"DataManager with pkhash {self.pkhash} with name {self.name}"

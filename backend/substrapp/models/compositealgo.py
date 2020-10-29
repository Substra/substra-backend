from django.db import models
import uuid
from substrapp.utils import get_hash


def upload_to(instance, filename):
    return 'compositealgos/{0}/{1}'.format(instance.key, filename)


class CompositeAlgo(models.Model):
    """Storage Data table"""
    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=upload_to, max_length=500)  # path max length to 500 instead of default 100
    description = models.FileField(upload_to=upload_to, max_length=500)  # path max length to 500 instead of default 100
    validated = models.BooleanField(default=False)
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        """Use hash of file as checksum"""
        if not self.checksum and self.file:
            self.checksum = get_hash(self.file)
        super(CompositeAlgo, self).save(*args, **kwargs)

    def __str__(self):
        return f"CompositeAlgo with key {self.key} with validated {self.validated}"

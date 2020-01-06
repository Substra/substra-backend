from django.db import models

from libs.timestamp_model import TimeStamped
from substrapp.utils import get_hash


def upload_to(instance, filename):
    return 'objectives/{0}/{1}'.format(instance.pk, filename)


class Objective(TimeStamped):
    """Storage Objective table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    validated = models.BooleanField(default=False, blank=True)
    description = models.FileField(upload_to=upload_to, max_length=500, blank=True, null=True)
    metrics = models.FileField(upload_to=upload_to, max_length=500, blank=True, null=True)

    def save(self, *args, **kwargs):
        """Use hash of description file as primary key"""
        if not self.pkhash:
            self.pkhash = get_hash(self.description)
        super(Objective, self).save(*args, **kwargs)

    def __str__(self):
        return f"Objective with pkhash {self.pkhash} with validated {self.validated}"

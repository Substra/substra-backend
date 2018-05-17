from django.db import models
from .utils import compute_hash


class DataOpener(models.Model):
    """Storage DataOpener table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    name = models.CharField(blank=True, max_length=24)
    script = models.FileField()

    def save(self, *args, **kwargs):
        """Use hash of description file as primary key"""
        if not self.pkhash:
            self.pkhash = compute_hash(self.script)
        super(DataOpener, self).save(*args, **kwargs)

    def __str__(self):
        return "%s %s" % (self.pkhash, self.name)

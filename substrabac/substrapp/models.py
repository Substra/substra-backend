from django.db import models
from .utils import compute_hash


# TODO for files?? b64.b64encode(zlib.compress(f.read())) ??
class Problem(models.Model):
    """Storage Problem table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    validated = models.BooleanField(default=False, blank=True)
    description = models.FileField()
    metrics = models.FileField()

    def save(self, *args, **kwargs):
        """Use hash of description file as primary key"""
        if not self.pkhash:
            self.pkhash = compute_hash(self.description)
        super(Problem, self).save(*args, **kwargs)

    def __str__(self):
        return "%s %s" % (self.pkhash, self.validated)


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


class Data(models.Model):
    """Storage Data table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    validated = models.BooleanField(default=False)
    features = models.FileField()
    labels = models.FileField()

    def save(self, *args, **kwargs):
        """Use hash of description file as primary key"""
        if not self.pkhash:
            self.pkhash = compute_hash(self.features)
        super(Data, self).save(*args, **kwargs)

    def __str__(self):
        return "%s %s" % (self.pkhash, self.validated)

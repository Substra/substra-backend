from django.db import models
from .utils import compute_hash


def upload_to(instance, filename):
    return 'datasets/{0}/{1}'.format(instance.pk, filename)


class Dataset(models.Model):
    """Storage Dataset table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    name = models.CharField(blank=True, max_length=24)
    data_opener = models.FileField(upload_to=upload_to, max_length=500)  # path max length to 500 instead of default 100
    description = models.FileField(upload_to=upload_to, max_length=500)  # path max length to 500 instead of default 100
    validated = models.BooleanField(default=False, blank=True)

    def save(self, *args, **kwargs):
        """Use hash of description file as primary key"""
        if not self.pkhash:
            self.pkhash = compute_hash(self.description)
        super(Dataset, self).save(*args, **kwargs)

    def __str__(self):
        return "Dataset with pkhash %(pkhash)s with name %(name)s" % {'pkhash': self.pkhash,
                                                                      'name': self.name}

from django.db import models
from .utils import compute_hash


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
        return "Data with pkhash %(pkhash)s with validated %(validated)s" % {'pkhash': self.pkhash,
                                                                             'validated': self.validated}

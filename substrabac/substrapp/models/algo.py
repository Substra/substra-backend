from django.db import models
from .utils import compute_hash


class Algo(models.Model):
    """Storage Data table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    validated = models.BooleanField(default=False)
    algo = models.FileField()

    def save(self, *args, **kwargs):
        """Use hash of description file as primary key"""
        if not self.pkhash:
            self.pkhash = compute_hash(self.algo)
        super(Algo, self).save(*args, **kwargs)

    def __str__(self):
        return "Algo with pkhash %(pkhash)s with validated %(validated)s" % {'pkhash': self.pkhash,
                                                                             'validated': self.validated}

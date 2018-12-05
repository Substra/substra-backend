from django.db import models

from substrapp.utils import get_hash


def upload_to(instance, filename):
    return 'algos/{0}/{1}'.format(instance.pk, filename)


class Algo(models.Model):
    """Storage Data table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    file = models.FileField(upload_to=upload_to, max_length=500)  # path max length to 500 instead of default 100
    description = models.FileField(upload_to=upload_to, max_length=500)  # path max length to 500 instead of default 100
    validated = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Use hash of file as primary key"""
        if not self.pkhash:
            self.pkhash = get_hash(self.file)
        super(Algo, self).save(*args, **kwargs)

    def __str__(self):
        return "Algo with pkhash %(pkhash)s with validated %(validated)s" % {'pkhash': self.pkhash,
                                                                             'validated': self.validated}

from django.db import models

from substrapp.utils import get_hash


def upload_to(instance, filename):
    return 'data/{0}/{1}'.format(instance.pk, filename)


class Data(models.Model):
    """Storage Data table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    validated = models.BooleanField(default=False)
    path = models.FilePathField(max_length=500, blank=True, null=True)  # path max length to 500 instead of default 100

    def save(self, *args, **kwargs):
        if not self.pkhash:
            self.pkhash = get_hash(self.file)
        super(Data, self).save(*args, **kwargs)

    def __str__(self):
        return f"Data with pkhash {self.pkhash} with validated {self.validated}"

    @property
    def get_file_url(self):
        return '.'
        #return 'data/{0}/{1}'.format(instance.pk, filename)

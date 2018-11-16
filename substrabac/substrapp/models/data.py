import logging
import shutil
import zipfile
from os import path, rename

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models

from substrapp.utils import get_hash

from django.db.models.signals import pre_save
from django.dispatch import receiver

from checksumdir import dirhash


def upload_to(instance, filename):
    return 'data/{0}/{1}'.format(instance.pk, filename)


class Data(models.Model):
    """Storage Data table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    validated = models.BooleanField(default=False)
    path = models.FilePathField(max_length=500, blank=True, null=True)  # path max length to 500 instead of default 100

    def save(self, *args, **kwargs):
        if not self.pkhash:
            self.pkhash = get_hash(self.path)
        super(Data, self).save(*args, **kwargs)

    def __str__(self):
        return f"Data with pkhash {self.pkhash} with validated {self.validated}"


@receiver(pre_save, sender=Data)
def data_pre_save(sender, instance, **kwargs):

    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'data/{0}'.format(instance.pk))

    # unzip file
    if isinstance(instance.path, InMemoryUploadedFile):
        try:
            zip_ref = zipfile.ZipFile(instance.path)
            zip_ref.extractall(directory)
            zip_ref.close()
        except Exception as e:
            logging.info(e)
        else:
            # calculate new hash
            sha256hash = dirhash(directory, 'sha256')
            # rename directory to new hash if does not exist
            new_directory = 'data/{0}'.format(sha256hash)
            try:
                rename(directory, path.join(getattr(settings, 'MEDIA_ROOT'), new_directory))
            except Exception as e:
                shutil.rmtree(directory)
                logging.error(e, exc_info=True)

            instance.pkhash = sha256hash
            instance.path = new_directory

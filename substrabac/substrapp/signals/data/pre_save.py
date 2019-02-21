import logging
import shutil
from os import path, rename

from checksumdir import dirhash
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from substrapp.utils import uncompress_path


def data_pre_save(sender, instance, **kwargs):
    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'data/{0}'.format(instance.pk))

    # unzip file
    if isinstance(instance.path, InMemoryUploadedFile):
        try:
            uncompress_path(instance.path, directory)
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
                # directory already exists with same exact data inside
                shutil.rmtree(directory)
                logging.error(e, exc_info=True)

            instance.pkhash = sha256hash
            instance.path = new_directory

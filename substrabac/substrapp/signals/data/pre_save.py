import logging
import shutil
from os import path, rename, link

from checksumdir import dirhash
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from substrapp.utils import uncompress_content


def data_pre_save(sender, instance, **kwargs):
    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'data/{0}'.format(instance.pk))

    # uncompress file if an archive
    if isinstance(instance.path, InMemoryUploadedFile):
        try:
            uncompress_content(instance.path.file.read(), directory)
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
                # created by a previous save, delete directory entitle pkhash
                # for avoiding duplicates
                shutil.rmtree(directory)
                logging.error(e, exc_info=True)

            # override defaults
            instance.pkhash = sha256hash
            instance.path = new_directory
    # make an hardlink if a path
    else:
        try:
            link(instance.path, directory)
        except:
            pass
        else:
            # override path for getting our hardlink
            instance.path = directory

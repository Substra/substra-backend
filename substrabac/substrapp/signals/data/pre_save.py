import shutil
import zipfile
from os import path

from checksumdir import dirhash
from django.conf import settings


def data_pre_save(sender, instance, **kwargs):
    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'data/{0}'.format(instance.pk))

    # unzip file
    zip_ref = zipfile.ZipFile(instance.path)
    zip_ref.extractall(directory)
    zip_ref.close()

    # calculate new hash
    sha256hash = dirhash(directory, 'sha256')
    # mv directory to new hash
    new_directory = 'data/{0}'.format(sha256hash)
    shutil.move(directory, path.join(getattr(settings, 'MEDIA_ROOT'), new_directory))

    # set hash and path
    instance.pkhash = sha256hash
    instance.path = new_directory
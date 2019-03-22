from os import path
from shutil import rmtree

from django.conf import settings


def data_post_delete(sender, instance, **kwargs):
    # remove created folder
    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'data', instance.pk)
    rmtree(directory)

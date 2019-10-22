from os import path
from shutil import rmtree

from django.conf import settings


def data_sample_post_delete(sender, instance, **kwargs):
    # remove created folder
    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'datasamples', instance.pk)
    if path.exists(directory):
        rmtree(directory)

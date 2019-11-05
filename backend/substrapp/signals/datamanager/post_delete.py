import shutil
from os import path
from django.conf import settings


def datamanager_post_delete(sender, instance, **kwargs):
    instance.data_opener.delete(False)
    instance.description.delete(False)

    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'datamanagers/{0}'.format(instance.pk))
    if path.exists(directory):
        shutil.rmtree(directory)

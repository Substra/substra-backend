import shutil
from os import path
from django.conf import settings


def metric_post_delete(sender, instance, **kwargs):
    instance.description.delete(False)
    instance.address.delete(False)

    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'metrics/{0}'.format(instance.key))
    if path.exists(directory):
        shutil.rmtree(directory)

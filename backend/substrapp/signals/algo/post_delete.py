import shutil
from os import path
from django.conf import settings


def algo_post_delete(sender, instance, **kwargs):
    instance.file.delete(False)
    instance.description.delete(False)

    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'algos/{0}'.format(instance.key))
    if path.exists(directory):
        shutil.rmtree(directory)

from os import path, rmdir
from django.conf import settings


def algo_post_delete(sender, instance, **kwargs):
    instance.file.delete(False)
    instance.description.delete(False)

    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'algos/{0}'.format(instance.pk))
    rmdir(directory)

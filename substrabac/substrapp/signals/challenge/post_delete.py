from os import path, rmdir
from django.conf import settings


def challenge_post_delete(sender, instance, **kwargs):
    instance.description.delete(False)
    instance.metrics.delete(False)

    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'challenges/{0}'.format(instance.pk))
    rmdir(directory)

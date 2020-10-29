import shutil
from os import path
from django.conf import settings


def objective_post_delete(sender, instance, **kwargs):
    instance.description.delete(False)
    instance.metrics.delete(False)

    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'objectives/{0}'.format(instance.key))
    if path.exists(directory):
        shutil.rmtree(directory)

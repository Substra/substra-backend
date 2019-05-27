import shutil
from os import path
from django.conf import settings


def model_post_delete(sender, instance, **kwargs):
    instance.file.delete(False)

    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'models/{0}'.format(instance.pk))
    shutil.rmtree(directory)

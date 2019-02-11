from os import path, rmdir
from django.conf import settings


def dataset_post_delete(sender, instance, **kwargs):
    instance.data_opener.delete(False)
    instance.description.delete(False)

    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'datasets/{0}'.format(instance.pk))
    rmdir(directory)

from os import path, link
from os.path import normpath
import shutil
from django.conf import settings


def data_sample_pre_save(sender, instance, **kwargs):
    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'datasamples/{0}'.format(instance.pk))

    # try to make an hard link to keep a free copy of the data
    # if not possible, keep the real path location
    try:
        shutil.copytree(normpath(instance.path), directory, copy_function=link)
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
    else:
        # override path for getting our hardlink
        instance.path = directory

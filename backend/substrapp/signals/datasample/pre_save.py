import logging
import shutil

from os import path, link
from os.path import normpath
from django.conf import settings


logger = logging.getLogger(__name__)


def data_sample_pre_save(sender, instance, **kwargs):
    destination_path = path.join(getattr(settings, 'MEDIA_ROOT'), 'datasamples/{0}'.format(instance.pk))
    src_path = normpath(instance.path)

    # try to make an hard link to keep a free copy of the data
    # if not possible, keep the real path location
    try:
        shutil.copytree(src_path, destination_path, copy_function=link)
    except Exception:
        logger.exception(f'error happened while copying data from {src_path} to {destination_path}')
        shutil.rmtree(destination_path, ignore_errors=True)
        logger.info(f'directory {destination_path} deleted')
    else:
        # override path for getting our hardlink
        instance.path = destination_path

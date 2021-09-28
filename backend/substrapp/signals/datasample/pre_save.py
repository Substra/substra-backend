import structlog
import shutil

from os import path, link
from os.path import normpath
from django.conf import settings


logger = structlog.get_logger(__name__)


def data_sample_pre_save(sender, instance, **kwargs):
    destination_path = path.join(getattr(settings, 'MEDIA_ROOT'), 'datasamples/{0}'.format(instance.key))
    src_path = normpath(instance.path)

    if path.exists(destination_path):
        raise FileExistsError(f'File exists: {destination_path}')

    # try to make an hard link to keep a free copy of the data
    # if not possible, keep the real path location
    try:
        shutil.copytree(src_path, destination_path, copy_function=link)
    except Exception:
        logger.error("Error while copying data", src=src_path, dest=destination_path)
        shutil.rmtree(destination_path, ignore_errors=True)
        logger.info("Directory deleted", directory=destination_path)
    else:
        # override path for getting our hardlink
        instance.path = destination_path

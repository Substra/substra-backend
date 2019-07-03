import logging
import shutil
from os import path, rename, link, walk, makedirs
from os.path import normpath

from checksumdir import dirhash
from django.conf import settings
from django.core.files import File

from substrapp.utils import uncompress_content


def create_hard_links(base_dir, directory):
    makedirs(directory, exist_ok=True)
    for root, subdirs, files in walk(base_dir):
        for file in files:
            link(path.join(root, file), path.join(directory, file))
        for subdir in subdirs:
            create_hard_links(root, subdir)


def data_sample_pre_save(sender, instance, **kwargs):
    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'datasamples/{0}'.format(instance.pk))

    # uncompress file if an archive
    # Should not be necessary with get_dir_hash
    if isinstance(instance.path, File):
        try:
            content = instance.path.read()
            instance.path.seek(0)
            uncompress_content(content, directory)
        except Exception as e:
            logging.exception(e)
            raise e
        else:
            # compute new hash
            sha256hash = dirhash(directory, 'sha256')
            # rename directory to new hash if does not exist
            new_directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'datasamples', sha256hash)
            try:
                rename(directory, new_directory)
            except OSError as e:
                # new_directory already exists with same exact data sample inside
                # created by a previous save, delete directory entitled pkhash
                # for avoiding duplicates
                shutil.rmtree(directory)
                logging.exception(e)

            # override defaults
            instance.pkhash = sha256hash
            instance.path = new_directory

    # make an hardlink on all files if a path
    else:
        # try to make an hard link to keep a free copy of the data
        # if not possible, keep the real path location
        try:
            create_hard_links(normpath(instance.path), directory)
        except Exception:
            pass
        else:
            # override path for getting our hardlink
            instance.path = directory

from os import path, link, walk, makedirs
from os.path import normpath

from django.conf import settings


def create_hard_links(base_dir, directory):
    makedirs(directory, exist_ok=True)
    for root, subdirs, files in walk(base_dir):
        for file in files:
            link(path.join(root, file), path.join(directory, file))
        for subdir in subdirs:
            create_hard_links(root, subdir)


def data_sample_pre_save(sender, instance, **kwargs):
    directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'datasamples/{0}'.format(instance.pk))

    # try to make an hard link to keep a free copy of the data
    # if not possible, keep the real path location
    try:
        create_hard_links(normpath(instance.path), directory)
    except Exception:
        pass
    else:
        # override path for getting our hardlink
        instance.path = directory

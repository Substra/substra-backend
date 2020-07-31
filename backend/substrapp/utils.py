import io
import hashlib
import logging
import os
import tempfile
from os import path
from os.path import isfile, isdir
import shutil

import requests
import tarfile
import zipfile
import uuid
import time

from checksumdir import dirhash

from django.conf import settings
from rest_framework import status

logger = logging.getLogger(__name__)


class JsonException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super(JsonException, self).__init__()


def get_dir_hash(dir):
    if not os.listdir(dir):
        raise Exception(f"Cannot compute hash of folder {dir}: folder is empty.")
    return dirhash(dir, 'sha256')


def get_archive_hash(archive_object):
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            content = archive_object.read()
            archive_object.seek(0)
            uncompress_content(content, temp_dir)
        except Exception as e:
            logger.error(e)
            raise e
        else:
            return get_dir_hash(temp_dir)


def store_datasamples_archive(archive_object):

    try:
        content = archive_object.read()
        archive_object.seek(0)
    except Exception as e:
        logger.error(e)
        raise e

    # Temporary directory for uncompress
    datasamples_uuid = uuid.uuid4().hex
    tmp_datasamples_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                                     f'datasamples/{datasamples_uuid}')
    try:
        uncompress_content(content, tmp_datasamples_path)
    except Exception as e:
        shutil.rmtree(tmp_datasamples_path, ignore_errors=True)
        logger.error(e)
        raise e
    else:
        # return the directory hash of the uncompressed file and the path of
        # the temporary directory. The removal should be handled externally.
        return get_dir_hash(tmp_datasamples_path), tmp_datasamples_path


def get_hash(file, key=None):
    if file is None:
        raise Exception(f"Can't get hash of file {file}: file is 'None'")

    if isinstance(file, (str, bytes, os.PathLike)):
        if isfile(file):
            with open(file, 'rb') as f:
                data = f.read()
        elif isdir(file):
            return get_dir_hash(file)
        else:
            return ''
    else:
        openedfile = file.open()
        data = openedfile.read()
        openedfile.seek(0)

    return compute_hash(data, key)


def get_owner():
    ledger_settings = getattr(settings, 'LEDGER')
    return ledger_settings['client']['msp_id']


def compute_hash(bytes, key=None):
    sha256_hash = hashlib.sha256()

    if isinstance(bytes, str):
        bytes = bytes.encode()

    if key is not None and isinstance(key, str):
        bytes += key.encode()

    sha256_hash.update(bytes)

    return sha256_hash.hexdigest()


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def raise_if_path_traversal(requested_paths, to_directory):
    # Inspired from https://stackoverflow.com/a/45188896

    # Get real path and ensure there is a suffix /
    # at the end of the path
    safe_directory = os.path.join(
        os.path.realpath(to_directory),
        ''
    )

    if not isinstance(requested_paths, list):
        raise TypeError(f'requested_paths argument should be a list not a {type(requested_paths)}')

    for requested_path in requested_paths:
        real_requested_path = os.path.realpath(requested_path)
        is_traversal = os.path.commonprefix([real_requested_path, safe_directory]) != safe_directory

        if is_traversal:
            raise Exception(f'Path Traversal Error : {requested_path} (real : {real_requested_path}) is not safe.')


class ZipFile(zipfile.ZipFile):
    """Override Zipfile to ensure unix file permissions are preserved.

    This is due to a python bug:
    https://bugs.python.org/issue15795

    Workaround from:
    https://stackoverflow.com/questions/39296101/python-zipfile-removes-execute-permissions-from-binaries
    """

    def extract(self, member, path=None, pwd=None):
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()

        ret_val = self._extract_member(member, path, pwd)
        attr = member.external_attr >> 16
        os.chmod(ret_val, attr)
        return ret_val


def uncompress_path(archive_path, to_directory):

    if zipfile.is_zipfile(archive_path):

        with ZipFile(archive_path, 'r') as zf:

            # Check no path traversal
            filenames = [os.path.join(to_directory, filename)
                         for filename in zf.namelist()]
            raise_if_path_traversal(filenames, to_directory)

            zf.extractall(to_directory)

    elif tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, 'r:*') as tf:

            # Check no path traversal
            filenames = [os.path.join(to_directory, filename)
                         for filename in tf.getnames()]
            raise_if_path_traversal(filenames, to_directory)

            tf.extractall(to_directory)
    else:
        raise Exception('Archive must be zip or tar.gz')


def uncompress_content(archive_content, to_directory):
    if zipfile.is_zipfile(io.BytesIO(archive_content)):
        with ZipFile(io.BytesIO(archive_content)) as zf:

            # Check no path traversal
            filenames = [os.path.join(to_directory, filename)
                         for filename in zf.namelist()]
            raise_if_path_traversal(filenames, to_directory)

            zf.extractall(to_directory)
    else:
        try:
            with tarfile.open(fileobj=io.BytesIO(archive_content)) as tf:

                # Check no path traversal
                filenames = [os.path.join(to_directory, filename)
                             for filename in tf.getnames()]
                raise_if_path_traversal(filenames, to_directory)

                tf.extractall(to_directory)
        except tarfile.TarError:
            raise Exception('Archive must be zip or tar.*')


class NodeError(Exception):
    pass


def get_remote_file(url, auth, content_dst_path=None, **kwargs):

    kwargs.update({
        'headers': {'Accept': 'application/json;version=0.0'},
        'auth': auth
    })

    if settings.DEBUG:
        kwargs['verify'] = False

    try:
        if kwargs.get('stream', False) and content_dst_path is not None:
            chunk_size = 1024 * 1024

            with requests.get(url, **kwargs) as response:
                response.raise_for_status()

                with open(content_dst_path, 'wb') as fp:
                    fp.writelines(response.iter_content(chunk_size))
        else:
            response = requests.get(url, **kwargs)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        raise NodeError(f'Failed to fetch {url}') from e

    return response


def get_remote_file_content(url, auth, content_hash, salt=None):

    response = get_remote_file(url, auth)

    if response.status_code != status.HTTP_200_OK:
        logger.error(response.text)
        raise NodeError(f'Url: {url} returned status code: {response.status_code}')

    computed_hash = compute_hash(response.content, key=salt)
    if computed_hash != content_hash:
        raise NodeError(f"url {url}: hash doesn't match {content_hash} vs {computed_hash}")
    return response.content


def get_and_put_remote_file_content(url, auth, content_hash, content_dst_path, salt=None):

    response = get_remote_file(url, auth, content_dst_path, stream=True)

    if response.status_code != status.HTTP_200_OK:
        logger.error(response.text)
        raise NodeError(f'Url: {url} returned status code: {response.status_code}')

    computed_hash = get_hash(content_dst_path, key=salt)
    if computed_hash != content_hash:
        raise NodeError(f"url {url}: hash doesn't match {content_hash} vs {computed_hash}")


def get_subtuple_directory(subtuple_key):
    return path.join(getattr(settings, 'MEDIA_ROOT'), 'subtuple', subtuple_key)


def get_chainkeys_directory(compute_plan_id):
    return path.join(getattr(settings, 'MEDIA_ROOT'), 'computeplan',
                     compute_plan_id, 'chainkeys')


def timeit(function):
    def timed(*args, **kw):
        ts = time.time()
        result = function(*args, **kw)
        elaps = (time.time() - ts) * 1000
        logger.info(f'{function.__name__} - elaps={elaps:.2f}ms')
        return result
    return timed

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

from checksumdir import dirhash

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import status
from node.models import OutgoingNode
from requests.auth import HTTPBasicAuth


class JsonException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super(JsonException, self).__init__()


def get_dir_hash(archive_object):
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            content = archive_object.read()
            archive_object.seek(0)
            uncompress_content(content, temp_dir)
        except Exception as e:
            logging.error(e)
            raise e
        else:
            return dirhash(temp_dir, 'sha256')


def store_datasamples_archive(archive_object):

    try:
        content = archive_object.read()
        archive_object.seek(0)
    except Exception as e:
        logging.error(e)
        raise e

    # Temporary directory for uncompress
    datasamples_uuid = uuid.uuid4().hex
    tmp_datasamples_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                                     f'datasamples/{datasamples_uuid}')
    try:
        uncompress_content(content, tmp_datasamples_path)
    except Exception as e:
        shutil.rmtree(tmp_datasamples_path, ignore_errors=True)
        logging.error(e)
        raise e
    else:
        # return the directory hash of the uncompressed file and the path of
        # the temporary directory. The removal should be handled externally.
        return dirhash(tmp_datasamples_path, 'sha256'), tmp_datasamples_path


def get_hash(file, key=None):
    if file is None:
        return ''
    else:
        if isinstance(file, (str, bytes, os.PathLike)):
            if isfile(file):
                with open(file, 'rb') as f:
                    data = f.read()
            elif isdir(file):
                return dirhash(file, 'sha256')
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
            zf.extractall(to_directory)
    elif tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, 'r:*') as tf:
            tf.extractall(to_directory)
    else:
        raise Exception('Archive must be zip or tar.gz')


def uncompress_content(archive_content, to_directory):
    if zipfile.is_zipfile(io.BytesIO(archive_content)):
        with ZipFile(io.BytesIO(archive_content)) as zf:
            zf.extractall(to_directory)
    else:
        try:
            with tarfile.open(fileobj=io.BytesIO(archive_content)) as tf:
                tf.extractall(to_directory)
        except tarfile.TarError:
            raise Exception('Archive must be zip or tar.*')


def is_archive(archive_content):

    if isinstance(archive_content, InMemoryUploadedFile):
        archive_content = archive_content.file.read()
    if zipfile.is_zipfile(io.BytesIO(archive_content)):
        return True
    else:
        try:
            tar = tarfile.open(fileobj=io.BytesIO(archive_content))
            tar.close()
            return True
        except tarfile.TarError:
            return False


class NodeError(Exception):
    pass


def get_from_node(url, node_id):

    kwargs = {
        'headers': {'Accept': 'application/json;version=0.0'},
    }

    try:
        outgoing = OutgoingNode.objects.get(node_id=node_id)
    except OutgoingNode.DoesNotExist:
        raise NodeError(f'Unauthorized to call node_id: {node_id}')

    try:
        response = requests.get(url, auth=HTTPBasicAuth(outgoing.node_id, outgoing.secret), **kwargs)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        raise NodeError(f'Failed to fetch {url}') from e
    else:
        if response.status_code != status.HTTP_200_OK:
            logging.error(response.text)
            raise NodeError(f'Url: {url} returned status code: {response.status_code}')

    return response


def get_remote_file(url, node_id, content_hash):
    response = get_from_node(url, node_id)
    computed_hash = compute_hash(response.content)

    if computed_hash != content_hash:
        msg = 'computed hash is not the same as the hosted file.' \
              'Please investigate for default of synchronization or corruption'
        raise Exception(msg)

    return response.content, computed_hash

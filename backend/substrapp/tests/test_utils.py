import os
import tempfile
import zipfile
from unittest import mock

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.utils import compute_hash
from substrapp.utils import get_hash
from substrapp.utils import get_remote_file_content
from substrapp.utils import uncompress_content

from .common import FakeRequest
from .common import get_sample_algo

CHANNEL = "mychannel"
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class UtilsTests(APITestCase):
    def setUp(self):
        self.subtuple_path = MEDIA_ROOT
        self.algo, self.algo_filename = get_sample_algo()

    def test_get_remote_file_content(self):
        content = "some remote content"
        checksum = compute_hash(content)
        remote_file = {
            "storage_address": "localhost",
            "checksum": checksum,
            "owner": "external_node_id",
        }

        with mock.patch("substrapp.utils.get_owner") as get_owner, mock.patch(
            "substrapp.utils.requests.get"
        ) as request_get:
            get_owner.return_value = "external_node_id"
            request_get.return_value = FakeRequest(content=content, status=status.HTTP_200_OK)

            content_remote = get_remote_file_content(CHANNEL, remote_file, "external_node_id", checksum)
            self.assertEqual(content_remote, content)

        with mock.patch("substrapp.utils.get_owner") as get_owner, mock.patch(
            "substrapp.utils.requests.get"
        ) as request_get:
            get_owner.return_value = "external_node_id"
            request_get.return_value = FakeRequest(content=content, status=status.HTTP_200_OK)

            with self.assertRaises(Exception):
                # contents (by hash) are different
                get_remote_file_content(CHANNEL, remote_file, "external_node_id", "fake_hash")

    def test_uncompress_content_tar(self):
        algo_content = self.algo.read()
        checksum = get_hash(self.algo)

        subtuple = {"key": checksum, "algo": "testalgo"}

        with mock.patch("substrapp.utils.get_hash") as mget_hash:
            mget_hash.return_value = checksum
            uncompress_content(algo_content, os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/'))

        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/algo.py')))
        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/Dockerfile')))

    def test_uncompress_content_zip(self):
        filename = "algo.py"
        filepath = os.path.join(self.subtuple_path, filename)
        with open(filepath, "w") as f:
            f.write("Hello World")
        self.assertTrue(os.path.exists(filepath))

        zipname = "sample.zip"
        zippath = os.path.join(self.subtuple_path, zipname)
        with zipfile.ZipFile(zippath, mode="w") as zf:
            zf.write(filepath, arcname=filename)
        self.assertTrue(os.path.exists(zippath))

        subtuple_key = "testkey"
        subtuple = {"key": subtuple_key, "algo": "testalgo"}

        with mock.patch("substrapp.utils.get_hash") as mget_hash:
            with open(zippath, "rb") as content:
                mget_hash.return_value = get_hash(zippath)
                uncompress_content(content.read(), os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/'))

        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/{filename}')))

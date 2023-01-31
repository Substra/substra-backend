import os
import tempfile
import zipfile
from unittest import mock

import pytest
from django.test import override_settings
from rest_framework.test import APITestCase

from substrapp import utils
from substrapp.utils import get_hash
from substrapp.utils import uncompress_content

from .common import get_sample_algo

CHANNEL = "mychannel"
SUBTUPLE_DIR = tempfile.mkdtemp()


@override_settings(SUBTUPLE_DIR=SUBTUPLE_DIR)
class UtilsTests(APITestCase):
    def setUp(self):
        self.subtuple_path = SUBTUPLE_DIR
        self.function, self.algo_filename = get_sample_algo()

    def test_uncompress_content_tar(self):
        algo_content = self.function.read()
        checksum = get_hash(self.function)

        subtuple = {"key": checksum, "function": "testalgo"}

        with mock.patch("substrapp.utils.get_hash") as mget_hash:
            mget_hash.return_value = checksum
            uncompress_content(algo_content, os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/'))

        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/function.py')))
        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/Dockerfile')))

    def test_uncompress_content_zip(self):
        filename = "function.py"
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
        subtuple = {"key": subtuple_key, "function": "testalgo"}

        with mock.patch("substrapp.utils.get_hash") as mget_hash:
            with open(zippath, "rb") as content:
                mget_hash.return_value = get_hash(zippath)
                uncompress_content(content.read(), os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/'))

        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/{filename}')))


def test_retry():
    @utils.retry(raise_exception=True)
    def test_raise():
        raise Exception("failure")

    @utils.retry()
    def test_do_not_raise():
        raise Exception("failure")

    with pytest.raises(Exception):
        test_raise()

    test_do_not_raise()

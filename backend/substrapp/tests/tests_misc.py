import tempfile
import shutil

from django.test import TestCase
from parameterized import parameterized

from mock import patch

from substrapp.utils import raise_if_path_traversal, uncompress_path

import os


DIRECTORY = '/tmp/testmisc/'
CHANNEL = 'mychannel'


class MockDevice():
    """A mock device to temporarily suppress output to stdout
    Similar to UNIX /dev/null.
    """

    def write(self, s):
        pass


class MockArchive:
    def __init__(self, traversal=True):
        if traversal:
            self.files = ['../../foo.csv', '../bar.csv']
        else:
            self.files = ['./', 'foo.csv', 'bar.csv']

    def __iter__(self):
        return iter(self.files)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            raise exc_val

    def namelist(self):
        return self.files

    def getnames(self):
        return self.files

    def extractall(self, path):
        pass


class MiscTests(TestCase):
    """Misc tests"""

    @parameterized.expand(
        [
            ("zip", True),
            ("tar", True),
            ("zip", False),
            ("tar", False),
        ]
    )
    def test_uncompress_path_path_traversal(self, format: str, traversal: bool):
        filename = "foo.csv"

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file_path = os.path.join(tmp_dir, filename)
            with open(tmp_file_path, "w") as f:
                f.write("bar")
            archive_path = shutil.make_archive(tmp_dir, format, root_dir=tmp_dir)

        with patch("substrapp.utils.zipfile.is_zipfile") as mock_is_zipfile, \
             patch("substrapp.utils.tarfile.is_tarfile") as mock_is_tarfile, \
             patch("substrapp.utils.ZipFile") as mock_zipfile, \
             patch("substrapp.utils.tarfile.open") as mock_tarfile:

            mock_is_zipfile.return_value = format == "zip"
            mock_is_tarfile.return_value = format == "tar"
            mock_zipfile.return_value = MockArchive(traversal)
            mock_tarfile.return_value = MockArchive(traversal)

            if traversal:
                with self.assertRaisesMessage(Exception, "Path Traversal Error"):
                    uncompress_path(archive_path, DIRECTORY)
            else:
                uncompress_path(archive_path, DIRECTORY)

    def test_uncompress_path_path_traversal_model(self):
        with self.assertRaises(Exception):
            model_dst_path = os.path.join(DIRECTORY, 'model/../../hackermodel')
            raise_if_path_traversal([model_dst_path], os.path.join(DIRECTORY, 'model/'))

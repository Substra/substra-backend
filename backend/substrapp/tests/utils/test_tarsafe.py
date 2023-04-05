import os
import tarfile
import tempfile

from django.test import TestCase

from substrapp.utils import tarsafe


class TarSafeTests(TestCase):
    """Test custom tarsafe override"""

    def test_raise_on_symlink(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # create the following tree structure:
            # ./Dockerfile
            # ./foo
            #    ./Dockerfile -> ../Dockerfile

            filename = "Dockerfile"
            symlink_source = os.path.join(tmpdir, filename)
            with open(symlink_source, "w") as fp:
                fp.write("FROM bar")

            archive_root = os.path.join(tmpdir, "foo")
            os.mkdir(archive_root)
            os.symlink(symlink_source, os.path.join(archive_root, filename))

            # create a tar archive of the foo folder
            tarpath = os.path.join(tmpdir, "foo.tgz")
            with tarfile.open(tarpath, "w:gz") as tar:
                for root, _dirs, files in os.walk(archive_root):
                    for file in files:
                        tar.add(os.path.join(root, file))

            with self.assertRaises(tarsafe.TarSafeError) as error:
                with tarsafe.open(tarpath, "r") as tar:
                    tar.extractall()

                self.assertIn("Unsupported symlink", str(error.exception))

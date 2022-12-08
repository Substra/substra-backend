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
                    def is_within_directory(directory, target):
                        
                        abs_directory = os.path.abspath(directory)
                        abs_target = os.path.abspath(target)
                    
                        prefix = os.path.commonprefix([abs_directory, abs_target])
                        
                        return prefix == abs_directory
                    
                    def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                    
                        for member in tar.getmembers():
                            member_path = os.path.join(path, member.name)
                            if not is_within_directory(path, member_path):
                                raise Exception("Attempted Path Traversal in Tar File")
                    
                        tar.extractall(path, members, numeric_owner=numeric_owner) 
                        
                    
                    safe_extract(tar)

                self.assertIn("Unsupported symlink", str(error.exception))

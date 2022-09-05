import os
import tempfile

from django.test import TestCase

from substrapp.utils.safezip import ZipFile

# This zip file was specifically crafted and contains empty files named:
# foo/bar
# ../foo/bar
# ../../foo/bar
# ../../../foo/bar
TRAVERSAL_ZIP = os.path.join(os.path.dirname(__file__), "data", "traversal.zip")

# This zip file was specifically crafted and contains:
# bar
# foo -> bar (symlink)
SYMLINK_ZIP = os.path.join(os.path.dirname(__file__), "data", "symlink.zip")


class ZipFileTests(TestCase):
    """Test custom ZipFile override"""

    def test_raise_on_path_traversal(self):
        zf = ZipFile(TRAVERSAL_ZIP, "r")
        with self.assertRaises(Exception) as cm:
            zf.extractall(tempfile.gettempdir())

        self.assertIn("Attempted directory traversal", str(cm.exception))

    def test_raise_on_symlink(self):
        zf = ZipFile(SYMLINK_ZIP, "r")
        with self.assertRaises(Exception) as cm:
            zf.extractall(tempfile.gettempdir())

        self.assertIn("Unsupported symlink", str(cm.exception))

import shutil
import tempfile
from io import StringIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase, override_settings
from .models import Problem, hash_upload


MEDIA_ROOT = tempfile.mkdtemp()


def get_temporary_text_file(contents, filename):
    """
    Creates a temporary text file

    :param contents: contents of the file
    :param filename: name of the file
    :type contents: str
    :type filename: str
    """
    io = StringIO()
    iolength = io.write(contents)
    text_file = InMemoryUploadedFile(io, None, filename, 'text',
                                     iolength, None)
    # Setting the file to its start
    text_file.seek(0)
    return text_file


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ModelTests(TestCase):
    """Model tests"""

    def setUp(self):
        pass

    def test_create_problem(self):
        description_content = "Super problem"
        metrics = "def metrics():\n\tpass"
        description = get_temporary_text_file(description_content,
                                              "description.md")
        metrics = get_temporary_text_file(metrics, "metrics.py")
        problem = Problem.objects.create(description=description,
                                         metrics=metrics)
        self.assertEqual(problem.pkhash, hash_upload(description))
# TODO APItest

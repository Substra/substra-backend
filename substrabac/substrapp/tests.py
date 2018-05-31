import shutil
import tempfile
from io import StringIO

from django.urls import reverse
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase, override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Problem, DataOpener, Data
from substrapp.models.utils import compute_hash

MEDIA_ROOT = tempfile.mkdtemp()


def get_temporary_text_file(contents, filename):
    """
    Creates a temporary text file

    :param contents: contents of the file
    :param filename: name of the file
    :type contents: str
    :type filename: str
    """
    f = StringIO()
    flength = f.write(contents)
    text_file = InMemoryUploadedFile(f, None, filename, 'text', flength, None)
    # Setting the file to its start
    text_file.seek(0)
    return text_file


# TODO for files?? b64.b64encode(zlib.compress(f.read())) ??

@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ModelTests(TestCase):
    """Model tests"""

    def setUp(self):
        pass

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT)

    def test_create_problem(self):
        description_content = "Super problem"
        metrics_content = "def metrics():\n\tpass"
        description = get_temporary_text_file(description_content,
                                              "description.md")
        metrics = get_temporary_text_file(metrics_content, "metrics.py")
        problem = Problem.objects.create(description=description,
                                         metrics=metrics)
        self.assertEqual(problem.pkhash, compute_hash(description))
        self.assertFalse(problem.validated)

    def test_create_data_opener(self):
        script_content = "Super problem"
        script = get_temporary_text_file(script_content, "read.py")
        data_opener = DataOpener.objects.create(script=script,
                                                name="slides_opener")
        self.assertEqual(data_opener.pkhash, compute_hash(script))

    def test_create_data(self):
        features_content = "2, 3, 4, 5\n10, 11, 12, 13\n21, 22, 23, 24"
        features = get_temporary_text_file(features_content, "features.csv")
        labels_content = "0\n1\n2"
        labels = get_temporary_text_file(labels_content, "labels.csv")
        data = Data.objects.create(features=features, labels=labels)
        self.assertEqual(data.pkhash, compute_hash(features))
        self.assertFalse(data.validated)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class QueryTests(APITestCase):

    def test_add_problem(self):
        url = reverse('substrapp:problem-list')

        description_content = 'My Super top problem'
        metrics_content = 'def metrics():\n\tpass'

        description = get_temporary_text_file(description_content, 'description.md')
        metrics = get_temporary_text_file(metrics_content, 'metrics.py')

        data = {
            'name': 'tough problem',
            'test_data': ['data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
                          'data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389'],
            'description': description,
            'metrics': metrics,
        }

        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r['pkhash'], '90f49bb9a9233d4ea55f516831a364047448e4b5e714dea1824a90b61e86a217')
        self.assertEqual(r['validated'], False)
        self.assertEqual(r['description'], 'http://testserver/problem/description.md')
        self.assertEqual(r['metrics'], 'http://testserver/problem/metrics.py')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

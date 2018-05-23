import shutil
import tempfile
from io import StringIO

from django.urls import reverse
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase, override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.models import Problem, DataOpener, Data
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

def get_sample_problem():
    description_content = "Super problem"
    description_filename = "description.md"
    description = get_temporary_text_file(description_content, description_filename)
    metrics_content = "def metrics():\n\tpass"
    metrics_filename = "metrics.py"
    metrics = get_temporary_text_file(metrics_content, metrics_filename)

    return description, description_filename, metrics, metrics_filename


def get_sample_dataopener():
    script_content = "import slidelib\n\ndef read():\n\tpass"
    script_filename = "read.py"
    script = get_temporary_text_file(script_content, script_filename)

    return script, script_filename


def get_sample_data():
    features_content = "2, 3, 4, 5\n10, 11, 12, 13\n21, 22, 23, 24"
    features_filename = "features.csv"
    features = get_temporary_text_file(features_content, features_filename)
    labels_content = "0\n1\n2"
    labels_filename = "labels.csv"
    labels = get_temporary_text_file(labels_content, labels_filename)

    return features, features_filename, labels, labels_filename


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ModelTests(TestCase):
    """Model tests"""

    def setUp(self):
        pass

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT)

    def test_create_problem(self):
        description, _, metrics, _ = get_sample_problem()
        problem = Problem.objects.create(description=description,
                                         metrics=metrics)
        self.assertEqual(problem.pkhash, compute_hash(description))
        self.assertFalse(problem.validated)

    def test_create_data_opener(self):
        script, _ = get_sample_dataopener()
        data_opener = DataOpener.objects.create(script=script, name="slides_opener")
        self.assertEqual(data_opener.pkhash, compute_hash(script))

    def test_create_data(self):
        features, _, labels, _ = get_sample_data()
        data = Data.objects.create(features=features, labels=labels)
        self.assertEqual(data.pkhash, compute_hash(features))
        self.assertFalse(data.validated)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class QueryTests(APITestCase):

    def setUp(self):
        self.problem_description, self.problem_description_filename,\
        self.problem_metrics, self.problem_metrics_filename = get_sample_problem()
        self.dataopener_script, self.dataopener_script_filename = get_sample_dataopener()
        self.data_features, self.data_features_filename, self.data_labels, self.data_labels_filename =\
            get_sample_data()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT)

    def test_add_problem(self):
        url = reverse('substrapp:problem-list')

        data = {
            'name': 'tough problem',
            'test_data': ['data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
                          'data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389'],
            'description': self.problem_description,
            'metrics': self.problem_metrics,
        }

        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r['pkhash'], compute_hash(self.problem_description))
        self.assertEqual(r['validated'], False)
        self.assertEqual(r['description'], 'http://testserver/problem/%s' % self.problem_description_filename)
        self.assertEqual(r['metrics'], 'http://testserver/problem/%s' % self.problem_metrics_filename)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_data_opener(self):
        url = reverse('substrapp:dataopener-list')

        data = {
            'name': 'slide opener',
            'script': self.dataopener_script
        }

        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r['pkhash'], compute_hash(self.dataopener_script))
        self.assertEqual(r['script'], 'http://testserver/dataopener/%s' % self.dataopener_script_filename)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_data(self):

        # add associated data opener
        dataopener_name = 'slide opener'
        DataOpener.objects.create(name=dataopener_name, script=self.dataopener_script)

        url = reverse('substrapp:data-list')

        data = {
            'features': self.data_features,
            'labels': self.data_labels,
            'name': 'liver slide',
            'problems': ['problem_%s' % compute_hash(self.problem_description)],
            'data_opener': dataopener_name,
            'permissions': 'all'
        }
        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r['pkhash'], compute_hash(self.data_features))
        self.assertEqual(r['features'], 'http://testserver/data/%s' % self.data_features_filename)
        self.assertEqual(r['labels'], 'http://testserver/data/%s' % self.data_labels_filename)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

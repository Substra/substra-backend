import shutil
import tempfile
from io import StringIO

from django.urls import reverse
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase, override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.models import Problem, DataOpener, Data, Algo
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


def get_sample_script():
    script_content = "import slidelib\n\ndef read():\n\tpass"
    script_filename = "script.py"
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
        script, _ = get_sample_script()
        data_opener = DataOpener.objects.create(script=script, name="slides_opener")
        self.assertEqual(data_opener.pkhash, compute_hash(script))

    def test_create_data(self):
        features, _, labels, _ = get_sample_data()
        data = Data.objects.create(features=features, labels=labels)
        self.assertEqual(data.pkhash, compute_hash(features))
        self.assertFalse(data.validated)

    def test_create_algo(self):
        script, _ = get_sample_script()
        algo = Algo.objects.create(algo=script)
        self.assertEqual(algo.pkhash, compute_hash(script))
        self.assertFalse(algo.validated)



# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class QueryTests(APITestCase):

    def setUp(self):
        self.problem_description, self.problem_description_filename,\
        self.problem_metrics, self.problem_metrics_filename = get_sample_problem()
        self.script, self.script_filename = get_sample_script()
        self.data_features, self.data_features_filename, self.data_labels, self.data_labels_filename =\
            get_sample_data()

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_add_problem_ok(self):
        url = reverse('substrapp:problem-list')

        data = {
            'name': 'tough problem',
            'test_data': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
                          '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389'],
            'description': self.problem_description,
            'metrics': self.problem_metrics,
        }

        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r['pkhash'], compute_hash(self.problem_description))
        self.assertEqual(r['validated'], False)
        self.assertEqual(r['description'], 'http://testserver/problem/%s' % self.problem_description_filename)
        self.assertEqual(r['metrics'], 'http://testserver/problem/%s' % self.problem_metrics_filename)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_problem_ko(self):
        url = reverse('substrapp:problem-list')

        data = {'name': 'empty problem'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'metrics': self.problem_metrics, 'description': self.problem_description}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_problem_no_version(self):
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

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_problem_wrong_version(self):
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

        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_dataopener_ok(self):
        url = reverse('substrapp:dataopener-list')

        data = {
            'name': 'slide opener',
            'script': self.script
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r['pkhash'], compute_hash(self.script))
        self.assertEqual(r['script'], 'http://testserver/dataopener/%s' % self.script_filename)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_dataopener_ko(self):
        url = reverse('substrapp:dataopener-list')

        data = {'name': 'toto'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_dataopener_no_version(self):
        url = reverse('substrapp:dataopener-list')

        data = {
            'name': 'slide opener',
            'script': self.script
        }
        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_dataopener_wrong_version(self):
        url = reverse('substrapp:dataopener-list')

        data = {
            'name': 'slide opener',
            'script': self.script
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_data_ok(self):

        # add associated data opener
        dataopener_name = 'slide opener'
        DataOpener.objects.create(name=dataopener_name, script=self.script)

        url = reverse('substrapp:data-list')

        data = {
            'features': self.data_features,
            'labels': self.data_labels,
            'name': 'liver slide',
            'problems': [compute_hash(self.problem_description)],
            'data_opener': dataopener_name,
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r['pkhash'], compute_hash(self.data_features))
        self.assertEqual(r['features'], 'http://testserver/data/%s' % self.data_features_filename)
        self.assertEqual(r['labels'], 'http://testserver/data/%s' % self.data_labels_filename)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_data_ko(self):
        url = reverse('substrapp:data-list')

        # missing data opener
        data = {'data_opener': 'not existing'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertEqual(r['message'], 'This DataOpener name does not exist.')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        dataopener_name = 'slide opener'
        DataOpener.objects.create(name=dataopener_name, script=self.script)

        # missing local storage field
        data = {'data_opener': dataopener_name,
                'name': 'liver slide', 'permissions': 'all',
                'problems': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379']}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # missing ledger field
        data = {'data_opener': dataopener_name, 'features': self.data_features, 'labels': self.data_labels}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_no_version(self):

        # add associated data opener
        dataopener_name = 'slide opener'
        DataOpener.objects.create(name=dataopener_name, script=self.script)

        url = reverse('substrapp:data-list')

        data = {
            'features': self.data_features,
            'labels': self.data_labels,
            'name': 'liver slide',
            'problems': [compute_hash(self.problem_description)],
            'data_opener': dataopener_name,
            'permissions': 'all'
        }
        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_data_wrong_version(self):

        # add associated data opener
        dataopener_name = 'slide opener'
        DataOpener.objects.create(name=dataopener_name, script=self.script)

        url = reverse('substrapp:data-list')

        data = {
            'features': self.data_features,
            'labels': self.data_labels,
            'name': 'liver slide',
            'problems': [compute_hash(self.problem_description)],
            'data_opener': dataopener_name,
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_algo_ok(self):

        # add associated problem
        Problem.objects.create(description=self.problem_description,
                               metrics=self.problem_metrics)

        url = reverse('substrapp:algo-list')

        data = {
            'algo': self.script,
            'name': 'super top algo',
            'problem': compute_hash(self.problem_description),
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r['pkhash'], compute_hash(self.script))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_algo_ko(self):
        url = reverse('substrapp:algo-list')

        # non existing associated problem
        data = {
            'algo': self.script,
            'name': 'super top algo',
            'problem': 'non existing problem',
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertIn('does not exist', r['message'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        Problem.objects.create(description=self.problem_description,
                               metrics=self.problem_metrics)

        # missing local storage field
        data = {
            'name': 'super top algo',
            'problem': compute_hash(self.problem_description),
            'permissions': 'all'
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # missing ledger field
        data = {
            'algo': self.script,
            'problem': compute_hash(self.problem_description),
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_algo_no_version(self):

        # add associated problem
        Problem.objects.create(description=self.problem_description,
                               metrics=self.problem_metrics)

        url = reverse('substrapp:algo-list')

        data = {
            'algo': self.script,
            'name': 'super top algo',
            'problem': compute_hash(self.problem_description),
            'permissions': 'all'
        }
        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_algo_wrong_version(self):

        # add associated problem
        Problem.objects.create(description=self.problem_description,
                               metrics=self.problem_metrics)

        url = reverse('substrapp:algo-list')

        data = {
            'algo': self.script,
            'name': 'super top algo',
            'problem': compute_hash(self.problem_description),
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_learnuplet_ok(self):
        # Add associated problem
        description, _, metrics, _ = get_sample_problem()
        Problem.objects.create(description=description,
                               metrics=metrics)
        # post data
        url = reverse('substrapp:learnuplet-list')

        data = {'problem': compute_hash(description),
                'train_data': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'model': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_learnuplet_ko(self):
        url = reverse('substrapp:learnuplet-list')

        data = {'problem': 'a' * 64,
                'train_data': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'model': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}

        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertIn('does not exist', r['message'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        Problem.objects.create(description=self.problem_description,
                               metrics=self.problem_metrics)
        data = {'problem': compute_hash(self.problem_description)}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_learnuplet_no_version(self):
        # Add associated problem
        description, _, metrics, _ = get_sample_problem()
        Problem.objects.create(description=description,
                               metrics=metrics)
        # post data
        url = reverse('substrapp:learnuplet-list')

        data = {'problem': compute_hash(description),
                'train_data': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'model': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}

        response = self.client.post(url, data, format='multipart')
        r = response.json()
        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_learnuplet_wrong_version(self):
        # Add associated problem
        description, _, metrics, _ = get_sample_problem()
        Problem.objects.create(description=description,
                               metrics=metrics)
        # post data
        url = reverse('substrapp:learnuplet-list')

        data = {'problem': compute_hash(description),
                'train_data': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'model': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_problem_metrics(self):
        problem = Problem.objects.create(description=self.problem_description,
                                         metrics=self.problem_metrics)
        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }
        response = self.client.get('/problem/%s/metrics/' % problem.pkhash, **extra)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        r = response.json()
        self.assertEqual(r, 'http://testserver/problem/%s/metrics/%s' % (problem.pkhash, self.problem_metrics_filename))

    def test_get_problem_metrics_no_version(self):
        problem = Problem.objects.create(description=self.problem_description,
                                         metrics=self.problem_metrics)
        response = self.client.get('/problem/%s/metrics/' % problem.pkhash)
        r = response.json()
        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_problem_metrics_wrong_version(self):
        problem = Problem.objects.create(description=self.problem_description,
                                         metrics=self.problem_metrics)
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.get('/problem/%s/metrics/' % problem.pkhash, **extra)
        r = response.json()
        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_algo_files(self):
        algo = Algo.objects.create(algo=self.script)
        extra = {
            'HTTP_ACCEPT': 'application/json;version=1.0',
        }
        response = self.client.get('/algo/%s/files/' % algo.pkhash, **extra)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        r = response.json()
        self.assertEqual(r, 'http://testserver/algo/%s/files/%s' % (algo.pkhash, self.script_filename))

    def test_get_algo_files_no_version(self):
        algo = Algo.objects.create(algo=self.script)
        response = self.client.get('/algo/%s/files/' % algo.pkhash)
        r = response.json()
        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_algo_files_wrong_version(self):
        algo = Algo.objects.create(algo=self.script)
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.get('/algo/%s/files/' % algo.pkhash, **extra)
        r = response.json()
        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


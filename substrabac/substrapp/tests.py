import os
import shutil
import tempfile
from io import StringIO

import mock

from django.urls import reverse
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase, override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.models import Challenge, Dataset, Data, Algo
from substrapp.models.utils import compute_hash, get_hash
from substrapp.serializers import LedgerChallengeSerializer, LedgerDatasetSerializer, LedgerAlgoSerializer, \
    LedgerDataSerializer, LedgerTrainTupleSerializer

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

def get_sample_challenge():
    description_content = "Super challenge"
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


def get_sample_dataset():
    description_content = "description"
    description_filename = "description.md"
    description = get_temporary_text_file(description_content, description_filename)
    data_opener_content = "import slidelib\n\ndef read():\n\tpass"
    data_opener_filename = "data_opener.py"
    data_opener = get_temporary_text_file(data_opener_content, data_opener_filename)

    return description, description_filename, data_opener, data_opener_filename


def get_sample_data():
    file_content = "0\n1\n2"
    file_filename = "file.csv"
    file = get_temporary_text_file(file_content, file_filename)

    return file, file_filename


def create(self):
    return {}, status.HTTP_201_CREATED


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ModelTests(TestCase):
    """Model tests"""

    def setUp(self):
        pass

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT)

    def test_create_challenge(self):
        description, _, metrics, _ = get_sample_challenge()
        challenge = Challenge.objects.create(description=description,
                                             metrics=metrics)

        self.assertEqual(challenge.pkhash, get_hash(description))
        self.assertFalse(challenge.validated)

    def test_create_dataset(self):
        description, _, data_opener, _ = get_sample_dataset()
        dataset = Dataset.objects.create(description=description, data_opener=data_opener, name="slides_opener")
        self.assertEqual(dataset.pkhash, get_hash(data_opener))

    def test_create_data(self):
        file, _ = get_sample_data()
        data = Data.objects.create(file=file)
        self.assertEqual(data.pkhash, get_hash(file))
        self.assertFalse(data.validated)

    def test_create_algo(self):
        script, _ = get_sample_script()
        algo = Algo.objects.create(file=script)
        self.assertEqual(algo.pkhash, get_hash(script))
        self.assertFalse(algo.validated)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class QueryTests(APITestCase):

    def setUp(self):
        self.challenge_description, self.challenge_description_filename, \
        self.challenge_metrics, self.challenge_metrics_filename = get_sample_challenge()
        self.script, self.script_filename = get_sample_script()
        self.data_file, self.data_file_filename = get_sample_data()
        self.data_description, self.data_description_filename, self.data_data_opener, self.data_opener_filename = get_sample_dataset()

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_add_challenge_ok(self):
        url = reverse('substrapp:challenge-list')

        data = {
            'name': 'tough challenge',
            'test_data_keys': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
                               '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389'],
            'description': self.challenge_description,
            'metrics': self.challenge_metrics,
            'permissions': 'all',
            'metrics_name': 'accuracy'
        }

        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerChallengeSerializer, 'create') as mocked_method:
            mocked_method.return_value = {
                                             'message': 'Challenge added in local db waiting for validation. The susbtra network has been notified for adding this Challenge'}, status.HTTP_200_OK
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r['pkhash'], get_hash(self.challenge_description))
            self.assertEqual(r['validated'], False)
            self.assertEqual(r['description'], 'http://testserver/media/challenges/%s/%s' % (
                r['pkhash'], self.challenge_description_filename))
            self.assertEqual(r['metrics'], 'http://testserver/media/challenges/%s/%s' % (
                r['pkhash'], self.challenge_metrics_filename))

            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_challenge_ko(self):
        url = reverse('substrapp:challenge-list')

        data = {'name': 'empty challenge'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'metrics': self.challenge_metrics, 'description': self.challenge_description}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_challenge_no_version(self):
        url = reverse('substrapp:challenge-list')

        description_content = 'My Super top challenge'
        metrics_content = 'def metrics():\n\tpass'

        description = get_temporary_text_file(description_content, 'description.md')
        metrics = get_temporary_text_file(metrics_content, 'metrics.py')

        data = {
            'name': 'tough challenge',
            'test_data_keys': ['data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
                               'data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389'],
            'description': description,
            'metrics': metrics,
        }

        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_challenge_wrong_version(self):
        url = reverse('substrapp:challenge-list')

        description_content = 'My Super top challenge'
        metrics_content = 'def metrics():\n\tpass'

        description = get_temporary_text_file(description_content, 'description.md')
        metrics = get_temporary_text_file(metrics_content, 'metrics.py')

        data = {
            'name': 'tough challenge',
            'test_data_keys': ['data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
                               'data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389'],
            'description': description,
            'metrics': metrics,
        }

        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_dataset_ok(self):
        url = reverse('substrapp:dataset-list')

        data = {
            'name': 'slide opener',
            'type': 'images',
            'permissions': 'all',
            'problem_keys': '',
            'description': self.data_description,
            'data_opener': self.data_data_opener
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerDatasetSerializer, 'create') as mocked_method:
            mocked_method.return_value = {
                                             'message': 'Dataset added in local db waiting for validation. The susbtra network has been notified for adding this Dataset'}, status.HTTP_200_OK

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r['pkhash'], get_hash(self.data_data_opener))
            self.assertEqual(r['description'],
                             'http://testserver/media/datasets/%s/%s' % (r['pkhash'], self.data_description_filename))

            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_dataset_ko(self):
        url = reverse('substrapp:dataset-list')

        data = {'name': 'toto'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_dataset_no_version(self):
        url = reverse('substrapp:dataset-list')

        data = {
            'name': 'slide opener',
            'description': self.data_description,
            'data_opener': self.data_data_opener
        }
        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_dataset_wrong_version(self):
        url = reverse('substrapp:dataset-list')

        data = {
            'name': 'slide opener',
            'type': 'images',
            'permissions': 'all',
            'problem_keys': '',
            'description': self.data_description,
            'data_opener': self.data_data_opener
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_data_ok(self):

        # add associated data opener
        dataset_name = 'slide opener'
        Dataset.objects.create(name=dataset_name, description=self.data_description, data_opener=self.data_data_opener)

        url = reverse('substrapp:data-list')

        data = {
            'file': self.data_file,
            'dataset_key': get_hash(self.data_data_opener),
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(os.path, 'getsize') as mocked_method:
            mocked_method.return_value = 100

            with mock.patch.object(LedgerDataSerializer, 'create') as mocked_method:
                mocked_method.return_value = {
                                                 'message': 'Data added in local db waiting for validation. The susbtra network has been notified for adding this Data'}, status.HTTP_200_OK

                response = self.client.post(url, data, format='multipart', **extra)
                r = response.json()
                self.assertEqual(r['pkhash'], get_hash(self.data_file))
                self.assertEqual(r['file'],
                                 'http://testserver/media/data/%s/%s' % (r['pkhash'], self.data_file_filename))

                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_data_ko(self):
        url = reverse('substrapp:data-list')

        # missing dataset
        data = {'dataset_key': 'not existing'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        with mock.patch.object(os.path, 'getsize') as mocked_method:
            mocked_method.return_value = 100

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['message'], 'This Dataset name does not exist.')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            dataset_name = 'slide opener'
            Dataset.objects.create(name=dataset_name, description=self.data_description,
                                   data_opener=self.data_data_opener)

            # missing local storage field
            data = {'dataset_key': get_hash(self.data_description),
                    'test_only': True, }
            response = self.client.post(url, data, format='multipart', **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # missing ledger field
            data = {'dataset_key': get_hash(self.data_description), 'file': self.script, }
            response = self.client.post(url, data, format='multipart', **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_no_version(self):

        # add associated data opener
        dataset_name = 'slide opener'
        Dataset.objects.create(name=dataset_name, description=self.data_description, data_opener=self.data_data_opener)

        url = reverse('substrapp:data-list')

        data = {
            'file': self.data_file,
            'dataset_key': get_hash(self.data_description),
            'test_only': True,
        }
        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_data_wrong_version(self):

        # add associated data opener
        dataset_name = 'slide opener'
        Dataset.objects.create(name=dataset_name, description=self.data_description, data_opener=self.data_data_opener)

        url = reverse('substrapp:data-list')

        data = {
            'file': self.script,
            'dataset_key': dataset_name,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_algo_ok(self):

        # add associated challenge
        Challenge.objects.create(description=self.challenge_description,
                                 metrics=self.challenge_metrics)

        url = reverse('substrapp:algo-list')

        data = {
            'file': self.script,
            'description': self.data_description,
            'name': 'super top algo',
            'challenge_key': get_hash(self.challenge_description),
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerAlgoSerializer, 'create') as mocked_method:
            mocked_method.return_value = {
                                             'message': 'Algo added in local db waiting for validation. The susbtra network has been notified for adding this Algo'}, status.HTTP_200_OK

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r['pkhash'], get_hash(self.script))
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_algo_ko(self):
        url = reverse('substrapp:algo-list')

        # non existing associated challenge
        data = {
            'file': self.script,
            'description': self.data_description,
            'name': 'super top algo',
            'challenge_key': 'non existing challenge',
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerAlgoSerializer, 'create') as mocked_method:
            mocked_method.return_value = {
                                             'message': 'Fail to add algo. Challenge does not exist'
                                         }, status.HTTP_400_BAD_REQUEST

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertIn('does not exist', r['message'])
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            Challenge.objects.create(description=self.challenge_description,
                                     metrics=self.challenge_metrics)

            # missing local storage field
            data = {
                'name': 'super top algo',
                'challenge_key': get_hash(self.challenge_description),
                'permissions': 'all'
            }
            response = self.client.post(url, data, format='multipart', **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # missing ledger field
            data = {
                'file': self.script,
                'description': self.data_description,
                'challenge_key': get_hash(self.challenge_description),
            }
            response = self.client.post(url, data, format='multipart', **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_algo_no_version(self):

        # add associated challenge
        Challenge.objects.create(description=self.challenge_description,
                                 metrics=self.challenge_metrics)

        url = reverse('substrapp:algo-list')

        data = {
            'file': self.script,
            'description': self.data_description,
            'name': 'super top algo',
            'challenge_key': get_hash(self.challenge_description),
            'permissions': 'all'
        }
        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_algo_wrong_version(self):

        # add associated challenge
        Challenge.objects.create(description=self.challenge_description,
                                 metrics=self.challenge_metrics)

        url = reverse('substrapp:algo-list')

        data = {
            'file': self.script,
            'description': self.data_description,
            'name': 'super top algo',
            'challenge_key': get_hash(self.challenge_description),
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_traintuple_ok(self):
        # Add associated challenge
        description, _, metrics, _ = get_sample_challenge()
        Challenge.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:traintuple-list')

        data = {'train_data_keys': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'model_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'algo_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerTrainTupleSerializer, 'create') as mocked_method:
            mocked_method.return_value = {
                                             'message': 'Traintuple added in local db waiting for validation. The susbtra network has been notified for adding this Traintuple'}, status.HTTP_200_OK

            response = self.client.post(url, data, format='multipart', **extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_traintuple_ko(self):
        url = reverse('substrapp:traintuple-list')

        data = {'train_data_keys': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'model_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}

        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertIn('This field may not be null.', r['algo_key'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        Challenge.objects.create(description=self.challenge_description,
                                 metrics=self.challenge_metrics)
        data = {'challenge': get_hash(self.challenge_description)}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_traintuple_no_version(self):
        # Add associated challenge
        description, _, metrics, _ = get_sample_challenge()
        Challenge.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:traintuple-list')

        data = {'train_data_keys': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'model_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'algo_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}

        response = self.client.post(url, data, format='multipart')
        r = response.json()
        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_traintuple_wrong_version(self):
        # Add associated challenge
        description, _, metrics, _ = get_sample_challenge()
        Challenge.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:traintuple-list')

        data = {'train_data_keys': ['5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'model_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'algo_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_challenge_metrics(self):
        challenge = Challenge.objects.create(description=self.challenge_description,
                                             metrics=self.challenge_metrics)
        with mock.patch('substrapp.views.utils.getObjectFromLedger') as mocked_function:
            mocked_function.return_value = self.challenge_metrics
            extra = {
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get('/challenge/%s/metrics/' % challenge.pkhash, **extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertNotEqual(challenge.pkhash, compute_hash(response.getvalue()))
            self.assertEqual(self.challenge_metrics_filename, response.filename)
            # self.assertEqual(r, 'http://testserver/media/challenges/%s/%s' % (
            #    challenge.pkhash, self.challenge_metrics_filename))

    def test_get_challenge_metrics_no_version(self):
        challenge = Challenge.objects.create(description=self.challenge_description,
                                             metrics=self.challenge_metrics)
        response = self.client.get('/challenge/%s/metrics/' % challenge.pkhash)
        r = response.json()
        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_challenge_metrics_wrong_version(self):
        challenge = Challenge.objects.create(description=self.challenge_description,
                                             metrics=self.challenge_metrics)
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.get('/challenge/%s/metrics/' % challenge.pkhash, **extra)
        r = response.json()
        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_algo_files(self):
        algo = Algo.objects.create(file=self.script)
        with mock.patch('substrapp.views.utils.getObjectFromLedger') as mocked_function:
            mocked_function.return_value = self.script
            extra = {
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get('/algo/%s/file/' % algo.pkhash, **extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(algo.pkhash, compute_hash(response.getvalue()))
            # self.assertEqual(r, 'http://testserver/media/algos/%s/%s' % (algo.pkhash, self.script_filename))

    def test_get_algo_files_no_version(self):
        algo = Algo.objects.create(file=self.script)
        response = self.client.get('/algo/%s/file/' % algo.pkhash)
        r = response.json()
        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_algo_files_wrong_version(self):
        algo = Algo.objects.create(file=self.script)
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.get('/algo/%s/file/' % algo.pkhash, **extra)
        r = response.json()
        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

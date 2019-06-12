import os
import shutil
import tempfile
import zipfile
from unittest.mock import MagicMock

import mock
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.models import Objective, DataManager, Algo, DataSample
from substrapp.serializers import LedgerObjectiveSerializer, \
    LedgerDataManagerSerializer, LedgerAlgoSerializer, \
    LedgerDataSampleSerializer, LedgerTrainTupleSerializer, DataSampleSerializer
from substrapp.utils import get_hash, compute_hash, get_dir_hash
from substrapp.views import DataSampleViewSet

from .common import get_sample_objective, get_sample_datamanager, \
    get_sample_zip_data_sample, get_sample_script, \
    get_temporary_text_file, get_sample_datamanager2, get_sample_algo, \
    get_sample_tar_data_sample, get_sample_zip_data_sample_2

MEDIA_ROOT = tempfile.mkdtemp()


# APITestCase

@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ObjectiveQueryTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        self.data_description, self.data_description_filename, self.data_data_opener, \
            self.data_opener_filename = get_sample_datamanager()

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def add_default_data_manager(self):
        DataManager.objects.create(name='slide opener',
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

    def get_default_objective_data(self):
        # XXX reload fixtures as it is an opened buffer and a post will
        #     modify the objects
        desc, _, metrics, _ = get_sample_objective()

        expected_hash = get_hash(self.objective_description)
        data = {
            'name': 'tough objective',
            'test_data_manager_key': get_hash(self.data_data_opener),
            'test_data_sample_keys': [
                '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
                '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389'],
            'description': desc,
            'metrics': metrics,
            'permissions': 'all',
            'metrics_name': 'accuracy'
        }
        return expected_hash, data

    def test_add_objective_sync_ok(self):
        self.add_default_data_manager()

        pkhash, data = self.get_default_objective_data()

        url = reverse('substrapp:objective-list')

        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerObjectiveSerializer, 'create') as mcreate:
            mcreate.return_value = {'pkhash': pkhash}, status.HTTP_201_CREATED

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r['pkhash'], pkhash)
            self.assertEqual(r['validated'], False)
            self.assertEqual(r['description'],
                             f'http://testserver/media/objectives/{r["pkhash"]}/{self.objective_description_filename}')
            self.assertEqual(r['metrics'],
                             f'http://testserver/media/objectives/{r["pkhash"]}/{self.objective_metrics_filename}')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_objective_conflict(self):
        self.add_default_data_manager()

        pkhash, data = self.get_default_objective_data()

        url = reverse('substrapp:objective-list')

        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerObjectiveSerializer, 'create') as mcreate:
            mcreate.return_value = {'pkhash': pkhash}, status.HTTP_201_CREATED

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r['pkhash'], pkhash)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # XXX reload data as the previous call to post change it
            _, data = self.get_default_objective_data()
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
            self.assertEqual(r['pkhash'], pkhash)

    def test_add_objective_no_sync_ok(self):
        # add associated data opener
        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        url = reverse('substrapp:objective-list')

        data = {
            'name': 'tough objective',
            'test_data_manager_key': get_hash(self.data_data_opener),
            'test_data_sample_keys': [
                '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
                '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389'],
            'description': self.objective_description,
            'metrics': self.objective_metrics,
            'permissions': 'all',
            'metrics_name': 'accuracy'
        }

        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        with mock.patch.object(LedgerObjectiveSerializer, 'create') as mcreate:
            mcreate.return_value = {'message': 'Objective added in local db waiting for validation. \
                                     The substra network has been notified for adding this Objective'}, status.HTTP_202_ACCEPTED
            response = self.client.post(url, data, format='multipart', **extra)
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_objective_ko(self):
        url = reverse('substrapp:objective-list')

        data = {'name': 'empty objective'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'metrics': self.objective_metrics,
                'description': self.objective_description}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_objective_no_version(self):
        url = reverse('substrapp:objective-list')

        description_content = 'My Super top objective'
        metrics_content = 'def metrics():\n\tpass'

        description = get_temporary_text_file(description_content,
                                              'description.md')
        metrics = get_temporary_text_file(metrics_content, 'metrics.py')

        data = {
            'name': 'tough objective',
            'test_data_sample_keys': [
                'data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
                'data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389'],
            'description': description,
            'metrics': metrics,
        }

        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_objective_wrong_version(self):
        url = reverse('substrapp:objective-list')

        description_content = 'My Super top objective'
        metrics_content = 'def metrics():\n\tpass'

        description = get_temporary_text_file(description_content,
                                              'description.md')
        metrics = get_temporary_text_file(metrics_content, 'metrics.py')

        data = {
            'name': 'tough objective',
            'test_data_sample_keys': [
                'data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
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

    def test_get_objective_metrics(self):
        objective = Objective.objects.create(
            description=self.objective_description,
            metrics=self.objective_metrics)
        with mock.patch(
                'substrapp.views.utils.getObjectFromLedger') as mgetObjectFromLedger:
            mgetObjectFromLedger.return_value = self.objective_metrics
            extra = {
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get(
                f'/objective/{objective.pkhash}/metrics/', **extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertNotEqual(objective.pkhash,
                                compute_hash(response.getvalue()))
            self.assertEqual(self.objective_metrics_filename,
                             response.filename)
            # self.assertEqual(r, f'http://testserver/media/objectives/{objective.pkhash}/{self.objective_metrics_filename}')

    def test_get_objective_metrics_no_version(self):
        objective = Objective.objects.create(
            description=self.objective_description,
            metrics=self.objective_metrics)
        response = self.client.get(f'/objective/{objective.pkhash}/metrics/')
        r = response.json()
        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_objective_metrics_wrong_version(self):
        objective = Objective.objects.create(
            description=self.objective_description,
            metrics=self.objective_metrics)
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.get(f'/objective/{objective.pkhash}/metrics/',
                                   **extra)
        r = response.json()
        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class DataManagerQueryTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.data_description, self.data_description_filename, self.data_data_opener, \
        self.data_opener_filename = get_sample_datamanager()

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_add_datamanager_sync_ok(self):
        url = reverse('substrapp:data_manager-list')

        data = {
            'name': 'slide opener',
            'type': 'images',
            'permissions': 'all',
            'objective_key': '',
            'description': self.data_description,
            'data_opener': self.data_data_opener
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerDataManagerSerializer, 'create') as mcreate:
            mcreate.return_value = {
                                       'pkhash': 'da920c804c4724f1ce7bd0484edcf4aafa209d5bd54e2e89972c087a487cbe02'}, status.HTTP_201_CREATED

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r['pkhash'], get_hash(self.data_data_opener))
            self.assertEqual(r['description'],
                             f'http://testserver/media/datamanagers/{r["pkhash"]}/{self.data_description_filename}')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_datamanager_no_sync_ok(self):
        url = reverse('substrapp:data_manager-list')
        data = {
            'name': 'slide opener',
            'type': 'images',
            'permissions': 'all',
            'objective_key': '',
            'description': self.data_description,
            'data_opener': self.data_data_opener
        }

        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        with mock.patch.object(LedgerDataManagerSerializer, 'create') as mcreate:
            mcreate.return_value = {'message': 'DataManager added in local db waiting for validation. \
                                     The substra network has been notified for adding this DataManager'}, status.HTTP_202_ACCEPTED
            response = self.client.post(url, data, format='multipart', **extra)

            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_datamanager_ko(self):
        url = reverse('substrapp:data_manager-list')

        data = {'name': 'toto'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_datamanager_no_version(self):
        url = reverse('substrapp:data_manager-list')

        data = {
            'name': 'slide opener',
            'description': self.data_description,
            'data_opener': self.data_data_opener
        }
        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_datamanager_wrong_version(self):
        url = reverse('substrapp:data_manager-list')

        data = {
            'name': 'slide opener',
            'type': 'images',
            'permissions': 'all',
            'objective_key': '',
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


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class DataSampleQueryTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.script, self.script_filename = get_sample_script()
        self.data_file, self.data_file_filename = get_sample_zip_data_sample()
        self.data_file_2, self.data_file_filename_2 = get_sample_zip_data_sample_2()
        self.data_tar_file, self.data_tar_file_filename = get_sample_tar_data_sample()

        self.data_description, self.data_description_filename, self.data_data_opener, \
        self.data_opener_filename = get_sample_datamanager()

        self.data_description2, self.data_description_filename2, self.data_data_opener2, \
        self.data_opener_filename2 = get_sample_datamanager2()

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_add_data_sample_sync_ok(self):

        # add associated data opener
        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        url = reverse('substrapp:data_sample-list')

        data = {
            'file': self.data_file,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:
            mcreate.return_value = {
                                       'pkhash': '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553',
                                       'validated': True}, status.HTTP_201_CREATED

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.data_file.file.seek(0)
            self.assertEqual(r[0]['pkhash'], get_dir_hash(self.data_file.file))

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_bulk_add_data_sample_sync_ok(self):

        # add associated data opener
        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        url = reverse('substrapp:data_sample-list')

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock2 = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = 'foo.zip'
        file_mock2.name = 'bar.zip'
        file_mock.read = MagicMock(return_value=self.data_file.read())
        file_mock2.read = MagicMock(return_value=self.data_file_2.read())

        data = {
            file_mock.name: file_mock,
            file_mock2.name: file_mock2,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.serializers.datasample.DataSampleSerializer.get_validators') as mget_validators, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:
            mget_validators.return_value = []
            self.data_file.seek(0)
            self.data_file_2.seek(0)
            ledger_data = {'pkhash': [get_dir_hash(file_mock), get_dir_hash(file_mock2)], 'validated': True}
            mcreate.return_value = ledger_data, status.HTTP_201_CREATED

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(len(r), 2)
            self.assertEqual(r[0]['pkhash'], get_dir_hash(file_mock))
            self.assertTrue(r[0]['path'].endswith(f'/datasamples/{get_dir_hash(file_mock)}'))
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_data_sample_no_sync_ok(self):
        # add associated data opener
        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)
        url = reverse('substrapp:data_sample-list')
        data = {
            'file': self.data_file,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        with mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:
            mcreate.return_value = {'message': 'Data added in local db waiting for validation. \
                                     The substra network has been notified for adding this Data'}, status.HTTP_202_ACCEPTED
            response = self.client.post(url, data, format='multipart', **extra)

            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_data_sample_ko(self):
        url = reverse('substrapp:data_sample-list')

        # missing datamanager
        data = {'data_manager_keys': ['toto']}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertEqual(r['message'],
                         "One or more datamanager keys provided do not exist in local substrabac database. Please create them before. DataManager keys: ['toto']")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        # missing local storage field
        data = {'data_manager_keys': [get_hash(self.data_description)],
                'test_only': True, }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # missing ledger field
        data = {'data_manager_keys': [get_hash(self.data_description)],
                'file': self.script, }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_already_exists(self):
        url = reverse('substrapp:data_sample-list')

        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = 'foo.zip'
        file_mock.read = MagicMock(return_value=self.data_file.file.read())
        file_mock.open = MagicMock(return_value=file_mock)

        d = DataSample(path=file_mock)
        # trigger pre save
        d.save()

        data = {
            'file': file_mock,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(zipfile, 'is_zipfile') as mis_zipfile:
            mis_zipfile.return_value = True
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['message'],
                             [[{'pkhash': ['data sample with this pkhash already exists.']}]])
            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_add_data_sample_ko_not_a_zip(self):
        url = reverse('substrapp:data_sample-list')

        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        file_mock = MagicMock(spec=File)
        file_mock.name = 'foo.zip'
        file_mock.read = MagicMock(return_value=b'foo')

        data = {
            'file': file_mock,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertEqual(r['message'], 'Archive must be zip or tar.*')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_408(self):
        url = reverse('substrapp:data_sample-list')

        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = 'foo.zip'
        file_mock.read = MagicMock(return_value=self.data_file.file.read())
        file_mock.open = MagicMock(return_value=file_mock)

        data = {
            'file': file_mock,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(zipfile, 'is_zipfile') as mis_zipfile, \
            mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:
            mcreate.return_value = {'pkhash': get_hash(file_mock), 'validated': False}, status.HTTP_408_REQUEST_TIMEOUT
            mis_zipfile.return_value = True
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['message'], {'pkhash': [get_dir_hash(file_mock)], 'validated': False})
            self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)

    def test_bulk_add_data_sample_ko_408(self):

        # add associated data opener
        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        url = reverse('substrapp:data_sample-list')

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock2 = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = 'foo.zip'
        file_mock2.name = 'bar.zip'
        file_mock.read = MagicMock(return_value=self.data_file.read())
        file_mock2.read = MagicMock(return_value=self.data_file_2.read())

        data = {
            file_mock.name: file_mock,
            file_mock2.name: file_mock2,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.serializers.datasample.DataSampleSerializer.get_validators') as mget_validators, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:
            mget_validators.return_value = []
            self.data_file.seek(0)
            self.data_tar_file.seek(0)
            ledger_data = {'pkhash': [get_dir_hash(file_mock), get_dir_hash(file_mock2)], 'validated': False}
            mcreate.return_value = ledger_data, status.HTTP_408_REQUEST_TIMEOUT

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['message']['validated'], False)
            self.assertEqual(DataSample.objects.count(), 2)
            self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)

    def test_bulk_add_data_sample_ko_same_pkhash(self):

        # add associated data opener
        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        url = reverse('substrapp:data_sample-list')

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock2 = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = 'foo.zip'
        file_mock2.name = 'bar.tar.gz'
        file_mock.read = MagicMock(return_value=self.data_file.read())
        file_mock2.read = MagicMock(return_value=self.data_tar_file.read())

        data = {
            file_mock.name: file_mock,
            file_mock2.name: file_mock2,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.serializers.datasample.DataSampleSerializer.get_validators') as mget_validators, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:
            mget_validators.return_value = []
            self.data_file.seek(0)
            self.data_tar_file.seek(0)
            ledger_data = {'pkhash': [get_dir_hash(file_mock), get_dir_hash(file_mock2)], 'validated': False}
            mcreate.return_value = ledger_data, status.HTTP_408_REQUEST_TIMEOUT

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(DataSample.objects.count(), 0)
            self.assertEqual(r['message'], f'Your data sample archives contain same files leading to same pkhash, please review the content of your achives. Archives {file_mock2.name} and {file_mock.name} are the same')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_400(self):
        url = reverse('substrapp:data_sample-list')

        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = 'foo.zip'
        file_mock.read = MagicMock(return_value=self.data_file.file.read())

        data = {
            'file': file_mock,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(zipfile, 'is_zipfile') as mis_zipfile, \
            mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:
            mcreate.return_value = 'Failed', status.HTTP_400_BAD_REQUEST
            mis_zipfile.return_value = True
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['message'], 'Failed')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_serializer_invalid(self):
        url = reverse('substrapp:data_sample-list')

        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = 'foo.zip'
        file_mock.read = MagicMock(return_value=self.data_file.read())

        data = {
            'file': file_mock,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(zipfile, 'is_zipfile') as mis_zipfile, \
            mock.patch.object(DataSampleViewSet, 'get_serializer') as mget_serializer:
            mocked_serializer = MagicMock(DataSampleSerializer)
            mocked_serializer.is_valid.return_value = True
            mocked_serializer.save.side_effect = Exception('Failed')
            mget_serializer.return_value = mocked_serializer

            mis_zipfile.return_value = True

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['message'], "Failed")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_ledger_invalid(self):
        url = reverse('substrapp:data_sample-list')

        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = 'foo.zip'
        file_mock.read = MagicMock(return_value=self.data_file.file.read())

        data = {
            'file': file_mock,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(zipfile, 'is_zipfile') as mis_zipfile, \
            mock.patch('substrapp.views.datasample.LedgerDataSampleSerializer', spec=True) as mLedgerDataSampleSerializer:
            mocked_LedgerDataSampleSerializer = MagicMock()
            mocked_LedgerDataSampleSerializer.is_valid.return_value = False
            mocked_LedgerDataSampleSerializer.errors = 'Failed'
            mLedgerDataSampleSerializer.return_value = mocked_LedgerDataSampleSerializer

            mis_zipfile.return_value = True
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['message'], "[ErrorDetail(string='Failed', code='invalid')]")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_no_version(self):

        # add associated data opener
        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        url = reverse('substrapp:data_sample-list')

        data = {
            'file': self.data_file,
            'data_manager_keys': [get_hash(self.data_description)],
            'test_only': True,
        }
        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_data_sample_wrong_version(self):

        # add associated data opener
        datamanager_name = 'slide opener'
        DataManager.objects.create(name=datamanager_name,
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        url = reverse('substrapp:data_sample-list')

        data = {
            'file': self.script,
            'data_manager_keys': [datamanager_name],
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_bulk_update_data(self):

        # add associated data opener
        datamanager = DataManager.objects.create(name='slide opener',
                                                 description=self.data_description,
                                                 data_opener=self.data_data_opener)
        datamanager2 = DataManager.objects.create(name='slide opener 2',
                                                  description=self.data_description2,
                                                  data_opener=self.data_data_opener2)

        d = DataSample(path=self.data_file)
        # trigger pre save
        d.save()

        url = reverse('substrapp:data_sample-bulk-update')

        data = {
            'data_manager_keys': [datamanager.pkhash, datamanager2.pkhash],
            'data_sample_keys': [d.pkhash],
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch(
                'substrapp.serializers.ledger.datasample.util.invokeLedger') as minvokeLedger:
            minvokeLedger.return_value = {'keys': [
                d.pkhash]}, status.HTTP_200_OK

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['keys'], [d.pkhash])
            self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AlgoQueryTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
        self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        self.algo, self.algo_filename = get_sample_algo()

        self.data_description, self.data_description_filename, self.data_data_opener, \
        self.data_opener_filename = get_sample_datamanager()

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_add_algo_sync_ok(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, '../../fixtures/chunantes/algos/algo3/algo.tar.gz'), 'rb') as tar_file:
            algo_content = tar_file.read()

        # add associated objective
        Objective.objects.create(description=self.objective_description,
                                 metrics=self.objective_metrics)

        url = reverse('substrapp:algo-list')

        data = {
            'file': self.algo,
            'description': self.data_description,
            'name': 'super top algo',
            'objective_key': get_hash(self.objective_description),
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerAlgoSerializer, 'create') as mcreate:
            mcreate.return_value = {'pkhash': compute_hash(algo_content)}, status.HTTP_201_CREATED

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r['pkhash'], compute_hash(algo_content))

    def test_add_algo_no_sync_ok(self):
        # add associated objective
        Objective.objects.create(description=self.objective_description,
                                 metrics=self.objective_metrics)
        url = reverse('substrapp:algo-list')
        data = {
            'file': self.algo,
            'description': self.data_description,
            'name': 'super top algo',
            'objective_key': get_hash(self.objective_description),
            'permissions': 'all'
        }

        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        with mock.patch.object(LedgerAlgoSerializer, 'create') as mcreate:
            mcreate.return_value = {'message': 'Algo added in local db waiting for validation. \
                                     The substra network has been notified for adding this Algo'}, status.HTTP_202_ACCEPTED
            response = self.client.post(url, data, format='multipart', **extra)

            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_algo_ko(self):
        url = reverse('substrapp:algo-list')

        # non existing associated objective
        data = {
            'file': self.algo,
            'description': self.data_description,
            'name': 'super top algo',
            'objective_key': 'non existing objectivexxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerAlgoSerializer, 'create') as mcreate:
            mcreate.return_value = {
                                       'message': 'Fail to add algo. Objective does not exist'}, status.HTTP_400_BAD_REQUEST

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertIn('does not exist', r['message'])
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            Objective.objects.create(description=self.objective_description,
                                     metrics=self.objective_metrics)

            # missing local storage field
            data = {
                'name': 'super top algo',
                'objective_key': get_hash(self.objective_description),
                'permissions': 'all'
            }
            response = self.client.post(url, data, format='multipart', **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # missing ledger field
            data = {
                'file': self.algo,
                'description': self.data_description,
                'objective_key': get_hash(self.objective_description),
            }
            response = self.client.post(url, data, format='multipart', **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_algo_no_version(self):

        # add associated objective
        Objective.objects.create(description=self.objective_description,
                                 metrics=self.objective_metrics)

        url = reverse('substrapp:algo-list')

        data = {
            'file': self.algo,
            'description': self.data_description,
            'name': 'super top algo',
            'objective_key': get_hash(self.objective_description),
            'permissions': 'all'
        }
        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_algo_wrong_version(self):

        # add associated objective
        Objective.objects.create(description=self.objective_description,
                                 metrics=self.objective_metrics)

        url = reverse('substrapp:algo-list')

        data = {
            'file': self.algo,
            'description': self.data_description,
            'name': 'super top algo',
            'objective_key': get_hash(self.objective_description),
            'permissions': 'all'
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_algo_files(self):
        algo = Algo.objects.create(file=self.algo)
        with mock.patch(
                'substrapp.views.utils.getObjectFromLedger') as mgetObjectFromLedger:
            mgetObjectFromLedger.return_value = self.algo
            extra = {
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get(f'/algo/{algo.pkhash}/file/', **extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(algo.pkhash, compute_hash(response.getvalue()))
            # self.assertEqual(r, f'http://testserver/media/algos/{algo.pkhash}/{self.algo_filename}')

    def test_get_algo_files_no_version(self):
        algo = Algo.objects.create(file=self.algo)
        response = self.client.get(f'/algo/{algo.pkhash}/file/')
        r = response.json()
        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_algo_files_wrong_version(self):
        algo = Algo.objects.create(file=self.algo)
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.get(f'/algo/{algo.pkhash}/file/', **extra)
        r = response.json()
        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TraintupleQueryTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
        self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_add_traintuple_ok(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:traintuple-list')

        data = {'train_data_sample_keys': [
            '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'algo_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'data_manager_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'objective_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'rank': -1,
                'FLtask_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'in_models_keys': [
                    '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422']}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerTrainTupleSerializer, 'create') as mcreate, \
                mock.patch('substrapp.views.traintuple.queryLedger') as mqueryLedger:

            raw_pkhash = 'traintuple_pkhash'.encode('utf-8').hex()
            mqueryLedger.return_value = ({'key': raw_pkhash}, status.HTTP_200_OK)
            mcreate.return_value = {'message': 'Traintuple added in local db waiting for validation. \
                                     The substra network has been notified for adding this Traintuple'}, status.HTTP_202_ACCEPTED

            response = self.client.post(url, data, format='multipart', **extra)

            print(response.json())
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_traintuple_ko(self):
        url = reverse('substrapp:traintuple-list')

        data = {'train_data_sample_keys': [
            '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'model_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}

        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertIn('This field may not be null.', r['algo_key'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        Objective.objects.create(description=self.objective_description,
                                 metrics=self.objective_metrics)
        data = {'objective': get_hash(self.objective_description)}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_traintuple_no_version(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:traintuple-list')

        data = {'train_data_sample_keys': [
            '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'datamanager_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'model_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'algo_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}

        response = self.client.post(url, data, format='multipart')
        r = response.json()
        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_traintuple_wrong_version(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:traintuple-list')

        data = {'train_data_sample_keys': [
            '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b422'],
                'datamanager_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'model_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088',
                'algo_key': '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0a088'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

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

from substrapp.models import DataManager, DataSample
from substrapp.serializers import LedgerDataSampleSerializer, DataSampleSerializer

from substrapp.utils import get_hash, get_dir_hash, store_datasamples_archive
from substrapp.ledger_utils import LedgerError, LedgerTimeout
from substrapp.views import DataSampleViewSet

from ..common import get_sample_datamanager, get_sample_zip_data_sample, get_sample_script, \
    get_sample_datamanager2, get_sample_tar_data_sample, get_sample_zip_data_sample_2, AuthenticatedClient

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
@override_settings(LEDGER_SYNC_ENABLED=True)
@override_settings(DEFAULT_DOMAIN='http://testserver')
class DataSampleQueryTests(APITestCase):
    client_class = AuthenticatedClient

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
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def add_default_data_manager(self):
        DataManager.objects.create(name='slide opener',
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

        DataManager.objects.create(name='slide opener',
                                   description=self.data_description2,
                                   data_opener=self.data_data_opener2)

    def get_default_datasample_data(self):
        expected_hash = get_dir_hash(self.data_file.file)
        self.data_file.file.seek(0)
        data = {
            'file': self.data_file,
            'data_manager_keys': [get_hash(self.data_data_opener)],
            'test_only': True,
        }

        return expected_hash, data

    def test_add_data_sample_sync_ok(self):

        self.add_default_data_manager()
        pkhash, data = self.get_default_datasample_data()

        url = reverse('substrapp:data_sample-list')
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.create_datasamples') as mcreate_ledger_assets:
            mcreate_ledger_assets.return_value = {
                'pkhash': pkhash,
                'validated': True
            }

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r[0]['pkhash'], pkhash)
            self.assertEqual(r[0]['validated'], True)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_bulk_add_data_sample_sync_ok(self):

        self.add_default_data_manager()

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
            'data_manager_keys': [get_hash(self.data_data_opener), get_hash(self.data_data_opener2)],
            'test_only': True,
        }
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.create_datasamples') as mcreate_ledger_assets:
            self.data_file.seek(0)
            self.data_file_2.seek(0)
            ledger_data = {'pkhash': [get_dir_hash(file_mock), get_dir_hash(file_mock2)], 'validated': True}
            mcreate_ledger_assets.return_value = ledger_data

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(len(r), 2)
            self.assertEqual(r[0]['pkhash'], get_dir_hash(file_mock))
            self.assertTrue(r[0]['path'].endswith(f'/datasamples/{get_dir_hash(file_mock)}'))
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(LEDGER_SYNC_ENABLED=False)
    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory'
    )
    def test_add_data_sample_no_sync_ok(self):
        self.add_default_data_manager()
        pkhash, data = self.get_default_datasample_data()

        url = reverse('substrapp:data_sample-list')
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.create_datasamples') as mcreate_ledger_assets:
            mcreate_ledger_assets.return_value = ''
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r[0]['pkhash'], pkhash)
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
        self.assertEqual(
            r['message'],
            "One or more datamanager keys provided do not exist in local database. "
            "Please create them before. DataManager keys: ['toto']")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.add_default_data_manager()

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

        self.add_default_data_manager()

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = 'foo.zip'
        file_mock.read = MagicMock(return_value=self.data_file.file.read())
        file_mock.open = MagicMock(return_value=file_mock)

        _, datasamples_path_from_file = store_datasamples_archive(file_mock)

        d = DataSample(path=datasamples_path_from_file)
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

        self.add_default_data_manager()

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

        self.add_default_data_manager()

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
            mcreate.side_effect = LedgerTimeout('Timeout')
            mis_zipfile.return_value = True
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(
                r['message'],
                {'pkhash': [get_dir_hash(file_mock)], 'validated': False})
            self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)

    def test_bulk_add_data_sample_ko_408(self):

        self.add_default_data_manager()

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
            mcreate.side_effect = LedgerTimeout('Timeout')

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['message']['validated'], False)
            self.assertEqual(DataSample.objects.count(), 2)
            self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)

    def test_bulk_add_data_sample_ko_same_pkhash(self):

        self.add_default_data_manager()

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
            self.assertEqual(
                r['message'],
                f'Your data sample archives contain same files leading to same pkhash, '
                f'please review the content of your achives. '
                f'Archives {file_mock2.name} and {file_mock.name} are the same')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_400(self):
        url = reverse('substrapp:data_sample-list')

        self.add_default_data_manager()

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
            mcreate.side_effect = LedgerError('Failed')
            mis_zipfile.return_value = True
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['message'], 'Failed')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_serializer_invalid(self):
        url = reverse('substrapp:data_sample-list')

        self.add_default_data_manager()

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

        self.add_default_data_manager()

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
                mock.patch('substrapp.views.datasample.LedgerDataSampleSerializer',
                           spec=True) as mLedgerDataSampleSerializer:  # noqa: N806
            mocked_LedgerDataSampleSerializer = MagicMock()  # noqa: N806
            mocked_LedgerDataSampleSerializer.is_valid.return_value = False
            mocked_LedgerDataSampleSerializer.errors = 'Failed'
            mLedgerDataSampleSerializer.return_value = mocked_LedgerDataSampleSerializer

            mis_zipfile.return_value = True
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['message'], "[ErrorDetail(string='Failed', code='invalid')]")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_no_version(self):

        self.add_default_data_manager()

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

        self.add_default_data_manager()

        url = reverse('substrapp:data_sample-list')

        data = {
            'file': self.script,
            'data_manager_keys': ['XXXX'],
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
                'substrapp.ledger.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = {'keys': [
                d.pkhash]}

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertEqual(r['keys'], [d.pkhash])
            self.assertEqual(response.status_code, status.HTTP_200_OK)

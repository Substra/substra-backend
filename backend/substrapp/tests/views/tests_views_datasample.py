import os
import shutil
import logging
import json

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase


from substrapp.serializers import LedgerDataSampleSerializer, DataSampleSerializer

from substrapp.views.datasample import path_leaf
from substrapp.utils import uncompress_content

from substrapp.models import DataManager

from ..common import get_sample_datamanager, FakeFilterDataManager, AuthenticatedClient
from ..assets import datamanager

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(DEFAULT_DOMAIN='https://localhost')
class DataSampleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.data_description, self.data_description_filename, \
            self.data_data_opener, self.data_opener_filename = get_sample_datamanager()

        self.extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        self.logger = logging.getLogger('django.request')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_data_create_bulk(self):
        url = reverse('substrapp:data_sample-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.join(dir_path, '../../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')
        data_path2 = os.path.join(dir_path, '../../../../fixtures/chunantes/datasamples/datasample0/0024899.zip')
        checksum1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'
        checksum2 = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'

        data = {
            'files': [path_leaf(data_path1), path_leaf(data_path2)],
            path_leaf(data_path1): open(data_path1, 'rb'),
            path_leaf(data_path2): open(data_path2, 'rb'),
            'json': json.dumps({
                'data_manager_keys': [datamanager[0]['key']],
                'test_only': False
            })
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate_ledger, \
                mock.patch.object(DataSampleSerializer, 'create', wraps=DataSampleSerializer().create) as mcreate:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mcreate_ledger.return_value = {'keys': ['some_key', 'some_other_key']}
            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(mcreate.call_args_list[0][0][0]['checksum'], checksum1)
        self.assertEqual(mcreate.call_args_list[1][0][0]['checksum'], checksum2)
        self.assertIsNotNone(response.data[0]['key'])
        self.assertIsNotNone(response.data[1]['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for x in data['files']:
            data[x].close()

    def test_data_create(self):
        url = reverse('substrapp:data_sample-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path = os.path.join(dir_path, '../../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')
        checksum = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'

        data = {
            'file': open(data_path, 'rb'),
            'json': json.dumps({
                'data_manager_keys': [datamanager[0]['key']],
                'test_only': False
            })
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate_ledger, \
                mock.patch.object(DataSampleSerializer, 'create', wraps=DataSampleSerializer().create) as mcreate:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mcreate_ledger.return_value = {'keys': ['some_key']}
            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(mcreate.call_args_list[0][0][0]['checksum'], checksum)
        self.assertIsNotNone(response.data[0]['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data['file'].close()

    def test_data_create_parent_path(self):
        url = reverse('substrapp:data_sample-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_zip_path = os.path.join(dir_path, '../../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')
        data_parent_path = os.path.join(MEDIA_ROOT, 'data_samples')
        data_path = os.path.join(data_parent_path, '0024700')

        with open(data_zip_path, 'rb') as data_zip:
            uncompress_content(data_zip.read(), data_path)

        checksum = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'

        data = {
            'path': data_parent_path,
            'data_manager_keys': [datamanager[0]['key']],
            'test_only': False,
            'multiple': True,
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate_ledger, \
                mock.patch.object(DataSampleSerializer, 'create', wraps=DataSampleSerializer().create) as mcreate:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mcreate_ledger.return_value = {'keys': ['some_key']}
            response = self.client.post(url, data=data, format='json', **self.extra)

        self.assertEqual(mcreate.call_args_list[0][0][0]['checksum'], checksum)
        self.assertIsNotNone(response.data[0]['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_data_create_path(self):
        url = reverse('substrapp:data_sample-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_zip_path = os.path.join(dir_path, '../../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')
        data_path = os.path.join(MEDIA_ROOT, '0024700')

        with open(data_zip_path, 'rb') as data_zip:
            uncompress_content(data_zip.read(), data_path)

        checksum = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'

        data = {
            'path': data_path,
            'data_manager_keys': [datamanager[0]['key']],
            'test_only': False
        }
        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate_ledger, \
                mock.patch.object(DataSampleSerializer, 'create', wraps=DataSampleSerializer().create) as mcreate:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mcreate_ledger.return_value = {'keys': ['some_key']}
            response = self.client.post(url, data=data, format='json', **self.extra)

        self.assertEqual(mcreate.call_args_list[0][0][0]['checksum'], checksum)
        self.assertIsNotNone(response.data[0]['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_datasamples_list(self):
        url = reverse('substrapp:data_sample-list')
        with mock.patch('substrapp.views.datasample.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [None, ['DataSampleA', 'DataSampleB']]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, ['DataSampleA', 'DataSampleB'])

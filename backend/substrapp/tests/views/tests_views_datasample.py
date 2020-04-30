import os
import shutil
import logging
import json

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase


from substrapp.serializers import LedgerDataSampleSerializer

from substrapp.views.datasample import path_leaf
from substrapp.utils import get_hash, uncompress_content

from substrapp.models import DataManager

from ..common import get_sample_datamanager, FakeFilterDataManager, AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
@override_settings(DEFAULT_DOMAIN='https://localhost')
@override_settings(LEDGER_SYNC_ENABLED=True)
class DataSampleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.data_description, self.data_description_filename, \
            self.data_data_opener, self.data_opener_filename = get_sample_datamanager()

        self.extra = {
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

        # dir hash
        pkhash1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'
        pkhash2 = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))]

        data = {
            'files': [path_leaf(data_path1), path_leaf(data_path2)],
            path_leaf(data_path1): open(data_path1, 'rb'),
            path_leaf(data_path2): open(data_path2, 'rb'),
            'json': json.dumps({
                'data_manager_keys': data_manager_keys,
                'test_only': False
            })
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mcreate.return_value = {'keys': [pkhash1, pkhash2]}
            response = self.client.post(url, data=data, format='multipart', **self.extra)
        self.assertEqual([r['pkhash'] for r in response.data], [pkhash1, pkhash2])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for x in data['files']:
            data[x].close()

    def test_data_create(self):
        url = reverse('substrapp:data_sample-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path = os.path.join(dir_path, '../../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')

        # dir hash
        pkhash = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))]

        data = {
            'file': open(data_path, 'rb'),
            'json': json.dumps({
                'data_manager_keys': data_manager_keys,
                'test_only': False
            })
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mcreate.return_value = {'keys': [pkhash]}
            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data[0]['pkhash'], pkhash)
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

        # dir hash
        pkhash = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))]

        data = {
            'path': data_parent_path,
            'data_manager_keys': data_manager_keys,
            'test_only': False,
            'multiple': True,
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mcreate.return_value = {'keys': [pkhash]}
            response = self.client.post(url, data=data, format='json', **self.extra)

        self.assertEqual(response.data[0]['pkhash'], pkhash)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_data_create_path(self):
        url = reverse('substrapp:data_sample-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_zip_path = os.path.join(dir_path, '../../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')
        data_path = os.path.join(MEDIA_ROOT, '0024700')

        with open(data_zip_path, 'rb') as data_zip:
            uncompress_content(data_zip.read(), data_path)

        # dir hash
        pkhash = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))]

        data = {
            'path': data_path,
            'data_manager_keys': data_manager_keys,
            'test_only': False
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mcreate.return_value = {'keys': [pkhash]}
            response = self.client.post(url, data=data, format='json', **self.extra)

        self.assertEqual(response.data[0]['pkhash'], pkhash)
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

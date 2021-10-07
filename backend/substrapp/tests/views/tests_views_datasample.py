import json
import ntpath

import logging
import mock
import os
import shutil
import tempfile

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.serializers import DataSampleSerializer

from orchestrator.client import OrchestratorClient

from substrapp.models import DataManager

from substrapp.utils import get_dir_hash

from ..common import get_sample_datamanager, FakeFilterDataManager, AuthenticatedClient
from ..assets import datamanager


MEDIA_ROOT = "/tmp/unittests_views/"
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURE_PATH = os.path.join(DIR_PATH, '../../../../fixtures/chunantes/datasamples')


def _get_archive_checksum(path):
    with tempfile.TemporaryDirectory() as tmp_path:
        shutil.unpack_archive(path, tmp_path)
        return get_dir_hash(tmp_path)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT,
                   LEDGER_CHANNELS={'mychannel': {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}})
@override_settings(DEFAULT_DOMAIN='https://localhost')
class DataSampleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.url = reverse('substrapp:data_sample-list')

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
        data_path1 = os.path.join(FIXTURE_PATH, 'datasample1/0024700.zip')
        data_path2 = os.path.join(FIXTURE_PATH, 'datasample0/0024899.zip')
        checksum1 = _get_archive_checksum(data_path1)
        checksum2 = _get_archive_checksum(data_path2)

        data = {
            'files': [path_leaf(data_path1), path_leaf(data_path2)],
            path_leaf(data_path1): open(data_path1, 'rb'),
            path_leaf(data_path2): open(data_path2, 'rb'),
            'json': json.dumps({
                'data_manager_keys': [datamanager[0]['key']],
                'test_only': False
            })
        }

        with mock.patch.object(DataManager.objects, 'filter', return_value=FakeFilterDataManager(1)), \
                mock.patch.object(OrchestratorClient, 'register_datasamples',
                                  return_value={}), \
                mock.patch.object(DataSampleSerializer, 'create', wraps=DataSampleSerializer().create):

            response = self.client.post(self.url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data[0]['checksum'], checksum1)
        self.assertEqual(response.data[1]['checksum'], checksum2)
        self.assertIsNotNone(response.data[0]['key'])
        self.assertIsNotNone(response.data[1]['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for x in data['files']:
            data[x].close()

    def test_data_create(self):
        data_path = os.path.join(FIXTURE_PATH, 'datasample1/0024700.zip')
        checksum = _get_archive_checksum(data_path)

        data = {
            'file': open(data_path, 'rb'),
            'json': json.dumps({
                'data_manager_keys': [datamanager[0]['key']],
                'test_only': False
            })
        }

        with mock.patch.object(DataManager.objects, 'filter', return_value=FakeFilterDataManager(1)), \
                mock.patch.object(OrchestratorClient, 'register_datasamples',
                                  return_value={}), \
                mock.patch.object(DataSampleSerializer, 'create', wraps=DataSampleSerializer().create):

            response = self.client.post(self.url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data[0]['checksum'], checksum)
        self.assertIsNotNone(response.data[0]['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data['file'].close()

    def test_data_create_parent_path(self):
        source_path = os.path.join(FIXTURE_PATH, 'datasample1/0024700.zip')
        parent_path = os.path.join(MEDIA_ROOT, 'data_samples')
        target_path = os.path.join(parent_path, '0024700')
        shutil.unpack_archive(source_path, target_path)
        checksum = get_dir_hash(target_path)

        data = {
            'path': parent_path,
            'data_manager_keys': [datamanager[0]['key']],
            'test_only': False,
            'multiple': True,
        }

        with mock.patch.object(DataManager.objects, 'filter', return_value=FakeFilterDataManager(1)), \
                mock.patch.object(OrchestratorClient, 'register_datasamples',
                                  return_value={}), \
                mock.patch.object(DataSampleSerializer, 'create', wraps=DataSampleSerializer().create):

            response = self.client.post(self.url, data=data, format='json', **self.extra)

        self.assertEqual(response.data[0]['checksum'], checksum)
        self.assertIsNotNone(response.data[0]['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_data_create_path(self):
        url = reverse('substrapp:data_sample-list')

        source_path = os.path.join(FIXTURE_PATH, 'datasample1/0024700.zip')
        target_path = os.path.join(MEDIA_ROOT, '0024700')
        shutil.unpack_archive(source_path, target_path)
        checksum = get_dir_hash(target_path)

        data = {
            'path': target_path,
            'data_manager_keys': [datamanager[0]['key']],
            'test_only': False
        }
        with mock.patch.object(DataManager.objects, 'filter', return_value=FakeFilterDataManager(1)), \
                mock.patch.object(OrchestratorClient, 'register_datasamples',
                                  return_value={}), \
                mock.patch.object(DataSampleSerializer, 'create', wraps=DataSampleSerializer().create):
            response = self.client.post(url, data=data, format='json', **self.extra)

        self.assertEqual(response.data[0]['checksum'], checksum)
        self.assertIsNotNone(response.data[0]['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_datasamples_list(self):
        url = reverse('substrapp:data_sample-list')
        with mock.patch.object(OrchestratorClient, 'query_datasamples',
                               side_effect=[[], ['DataSampleA', 'DataSampleB']]):

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 0, 'next': None, 'previous': None, 'results': []})

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 2, 'next': None, 'previous': None, 'results': ['DataSampleA', 'DataSampleB']})


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

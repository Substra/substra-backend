import os
import shutil
import tempfile
import json
import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from grpc import StatusCode

from substrapp.models import Algo
from substrapp.serializers import OrchestratorAlgoSerializer
from substrapp.utils import compute_hash
from substrapp.orchestrator.api import OrchestratorClient
from substrapp.orchestrator.error import OrcError

from ..common import (get_sample_datamanager, get_sample_algo, get_sample_algo_zip,
                      AuthenticatedClient, get_sample_algo_metadata)

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT,
                   LEDGER_CHANNELS={'mychannel': {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}})
class AlgoQueryTests(APITestCase):
    client_class = AuthenticatedClient
    objective_key = None

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.url = reverse('substrapp:algo-list')
        self.algo, self.algo_filename = get_sample_algo()
        self.algo_zip, self.algo_filename_zip = get_sample_algo_zip()

        self.data_description, self.data_description_filename, self.data_data_opener, \
            self.data_opener_filename = get_sample_datamanager()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def get_default_algo_data(self):
        return {
            'file': self.algo,
            'description': self.data_description,  # fake it
            'json': json.dumps({
                'metadata': {},
                'name': 'super top algo',
                'permissions': {
                    'public': True,
                    'authorized_ids': []
                }
            })
        }

    def get_default_algo_data_zip(self):
        return {
            'file': self.algo_zip,
            'description': self.data_description,  # fake it
            'json': json.dumps({
                'metadata': {},
                'name': 'super top algo',
                'permissions': {
                    'public': True,
                    'authorized_ids': []
                }
            })
        }

    def test_add_algo_ok(self):
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(OrchestratorClient, 'register_algo', return_value={'key': 'some key'}):
            response = self.client.post(self.url, self.get_default_algo_data_zip(), format='multipart', **extra)
            self.assertIsNotNone(response.json()['key'])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_algo_ko(self):

        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        error = OrcError()
        error.details = 'OE0006'
        error.code = StatusCode.ALREADY_EXISTS

        # already exists
        with mock.patch.object(OrchestratorAlgoSerializer, 'create', side_effect=error):
            response = self.client.post(self.url, self.get_default_algo_data(), format='multipart', **extra)
            self.assertIn('OE0006', response.json()['message'])
            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        # missing local storage field
        data = {
            'metadata': {},
            'name': 'super top algo',
            'permissions': {
                'public': True,
                'authorized_ids': []
            }
        }
        response = self.client.post(self.url, data, format='json', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # missing orchestrator field
        data = {
            'file': self.algo,
            'description': self.data_description,
            'json': json.dumps({
                'metadata': {},
                'name': 'super top algo',
            })
        }
        response = self.client.post(self.url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_algo_files(self):
        algo = Algo.objects.create(file=self.algo)
        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch.object(OrchestratorClient, 'query_algo', return_value=get_sample_algo_metadata()):

            extra = {
                'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get(f'/algo/{algo.key}/file/', **extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(algo.checksum, compute_hash(response.getvalue()))

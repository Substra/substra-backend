import os
import shutil
import tempfile
import json

import mock


from django.urls import reverse
from django.test import override_settings

from parameterized import parameterized

from rest_framework import status
from rest_framework.test import APITestCase
from substrapp.serializers import OrchestratorObjectiveSerializer

from substrapp.models import Objective, DataManager
from substrapp.orchestrator.api import OrchestratorClient
from substrapp.orchestrator.error import OrcError
from grpc import StatusCode

from ..common import get_sample_objective, get_sample_datamanager, \
    AuthenticatedClient, get_sample_objective_metadata

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT,
                   LEDGER_CHANNELS={'mychannel': {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}})
@override_settings(DEFAULT_DOMAIN='http://testserver')
class ObjectiveQueryTests(APITestCase):
    client_class = AuthenticatedClient
    data_manager_key = None

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        self.data_description, self.data_description_filename, self.data_data_opener, \
            self.data_opener_filename = get_sample_datamanager()

        self.test_data_sample_keys = [
            '5c1d9cd1-c2c1-082d-de09-21b56d11030c',
            '5c1d9cd1-c2c1-082d-de09-21b56d11030d']

        self.url = reverse('substrapp:objective-list')

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def add_default_data_manager(self):
        dm = DataManager.objects.create(name='slide opener',
                                        description=self.data_description,
                                        data_opener=self.data_data_opener)
        self.data_manager_key = str(dm.key)

    def get_default_objective_data(self, with_test_data_manager=True):

        json_ = {
            'name': 'tough objective',
            'test_data_sample_keys': self.test_data_sample_keys,
            'permissions': {
                'public': True,
                'authorized_ids': [],
            },
            'metrics_name': 'accuracy'
        }
        if with_test_data_manager:
            json_['test_data_manager_key'] = self.data_manager_key

        return {
            'description': self.objective_description,
            'metrics': self.objective_metrics,
            'json': json.dumps(json_),
        }

    @parameterized.expand([
        ("with_test_data_manager", True),
        ("without_test_data_manager", False)
    ])
    def test_add_objective_ok(self, _, with_test_data_manager):
        self.add_default_data_manager()
        data = self.get_default_objective_data(with_test_data_manager)

        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(OrchestratorClient, 'register_objective', return_value={'key': 'some key'}):
            response = self.client.post(self.url, data, format='multipart', **extra)
            self.assertIsNotNone(response.json()['key'])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_objective_ko(self):
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        error = OrcError()
        error.details = 'OE0006'
        error.code = StatusCode.ALREADY_EXISTS

        # already exists
        with mock.patch.object(OrchestratorObjectiveSerializer, 'create', side_effect=error):
            response = self.client.post(self.url, self.get_default_objective_data(), format='multipart', **extra)
            self.assertIn('OE0006', response.json()['message'])
            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        data = {'name': 'empty objective'}
        response = self.client.post(self.url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'metrics': self.objective_metrics,
                'description': self.objective_description}
        response = self.client.post(self.url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_objective_metrics(self):
        objective = Objective.objects.create(
            description=self.objective_description,
            metrics=self.objective_metrics)

        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch.object(OrchestratorClient, 'query_objective', return_value=get_sample_objective_metadata()):

            extra = {
                'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get(
                f'/objective/{objective.key}/metrics/', **extra)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(self.objective_metrics_filename,
                             response.filename)

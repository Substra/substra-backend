import os
import shutil
import logging
import zipfile
import copy
import json

import mock
import unittest
from parameterized import parameterized

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from orchestrator.client import OrchestratorClient
from grpc import RpcError, StatusCode

from ..common import get_sample_objective, AuthenticatedClient, encode_filter
from ..assets import objective, datamanager, model

MEDIA_ROOT = "/tmp/unittests_views/"
CHANNEL = 'mychannel'


def zip_folder(path, destination):
    zipf = zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for f in files:
            abspath = os.path.join(root, f)
            archive_path = os.path.relpath(abspath, start=path)
            zipf.write(abspath, arcname=archive_path)
    zipf.close()


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT,
                   LEDGER_CHANNELS={'mychannel': {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}})
@override_settings(DEFAULT_DOMAIN='https://localhost')
class ObjectiveViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.url = reverse('substrapp:objective-list')
        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        self.test_data_sample_keys = [
            "2d0f943a-a81a-9cb3-fe84-b162559ce6af",
            "533ee6e7-b9d8-b247-e7e8-53b24547f57e"
        ]

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

    def test_objective_list_empty(self):
        with mock.patch.object(OrchestratorClient, 'query_objectives', return_value=[]):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 0, 'next': None, 'previous': None, 'results': []})

    def test_objective_list_success(self):
        with mock.patch.object(OrchestratorClient, 'query_objectives', return_value=objective):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r['results'], objective)

    def test_objective_list_filter_fail(self):
        with mock.patch.object(OrchestratorClient, 'query_objectives', return_value=objective):
            search_params = '?search=challenERRORge'
            response = self.client.get(self.url + search_params, **self.extra)
            self.assertIn('Malformed search filters', response.json()['message'])

    def test_objective_list_filter_name(self):
        name_to_filter = encode_filter(objective[0]['name'])
        with mock.patch.object(OrchestratorClient, 'query_objectives', return_value=objective):
            search_params = f'?search=objective%253Aname%253A{name_to_filter}'
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 1)

    def test_objective_list_filter_metrics(self):
        with mock.patch.object(OrchestratorClient, 'query_objectives', return_value=objective):
            search_params = '?search=objective%253Ametrics%253Atest%2520metrics'
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), len(objective))

    def test_objective_list_filter_datamanager(self):
        datamanager_key = objective[0]['data_manager_key']
        datamanager_to_filter = encode_filter([dm for dm in datamanager
                                               if dm['key'] == datamanager_key].pop()['name'])
        with mock.patch.object(OrchestratorClient, 'query_objectives', return_value=objective), \
                mock.patch.object(OrchestratorClient, 'query_datamanagers', return_value=datamanager):
            search_params = f'?search=dataset%253Aname%253A{datamanager_to_filter}'
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 1)

    @unittest.skip("filter on model key does not work anymore")
    def test_objective_list_filter_model(self):
        with mock.patch.object(OrchestratorClient, 'query_objectives', return_value=objective), \
                mock.patch.object(OrchestratorClient, 'query_models', return_value=model):

            search_params = f'?search=model%253Akey%253A{model[0]}'
            response = self.client.get(self.url + search_params, **self.extra)

            self.assertEqual(len(response.json()), 1)

    def test_objective_retrieve(self):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../../../../fixtures/owkin/objectives/objective0/description.md'), 'rb') as f:
            content = f.read()

        with mock.patch.object(OrchestratorClient, 'query_objective', return_value=objective[0]), \
                mock.patch('substrapp.views.objective.get_remote_asset', return_value=content):
            response = self.client.get(f'{self.url}{objective[0]["key"]}/', **self.extra)
            self.assertEqual(response.json(), objective[0])

    def test_objective_retrieve_fail(self):
        # Key < 32 chars
        search_params = '12312323/'
        response = self.client.get(self.url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = 'X' * 32 + '/'
        response = self.client.get(self.url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = RpcError()
        error.details = 'out of range test'
        error.code = lambda: StatusCode.OUT_OF_RANGE

        with mock.patch.object(OrchestratorClient, 'query_objective', side_effect=error):
            response = self.client.get(f'{self.url}{objective[0]["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_objective_create(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        objective_path = os.path.join(dir_path, '../../../../fixtures/owkin/objectives/objective0/')
        description_path = os.path.join(objective_path, 'description.md')
        metrics_path = os.path.join(MEDIA_ROOT, 'metrics.zip')
        zip_folder(objective_path, metrics_path)

        data = {
            'json': json.dumps({
                'name': 'Simplified skin lesion classification',
                'metrics_name': 'macro-average recall',
                'permissions': {
                    'public': True,
                    'authorized_ids': [],
                },
                'test_data_sample_keys': self.test_data_sample_keys,
                'test_data_manager_key': datamanager[0]['key'],
            }),
            'description': open(description_path, 'rb'),
            'metrics': open(metrics_path, 'rb'),
        }

        with mock.patch.object(OrchestratorClient, 'register_objective', return_value={}):
            response = self.client.post(self.url, data=data, format='multipart', **self.extra)
        self.assertIsNotNone(response.data['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data['description'].close()
        data['metrics'].close()

    def test_objective_leaderboard_sort(self):
        url = reverse('substrapp:objective-leaderboard', args=[objective[0]['key']])
        with mock.patch.object(OrchestratorClient, 'query_objective_leaderboard', return_value={}) as mk:

            self.client.get(url, data={'sort': 'desc'}, **self.extra)
            mk.assert_called_with(
                objective[0]['key'],
                'desc',
            )

            self.client.get(url, data={'sort': 'asc'}, **self.extra)
            mk.assert_called_with(
                objective[0]['key'],
                'asc',
            )

        response = self.client.get(url, data={'sort': 'foo'}, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_objective_list_storage_addresses_update(self):

        # mock content
        o_objectives = copy.deepcopy(objective)
        for obj in o_objectives:
            for field in ('description', 'metrics'):
                obj[field]['storage_address'] = \
                    obj[field]['storage_address'] \
                    .replace('http://testserver', 'http://remotetestserver')

        with mock.patch.object(OrchestratorClient, 'query_objectives', return_value=o_objectives), \
                mock.patch('substrapp.views.objective.get_remote_asset', return_value=b'dummy binary content'):
            response = self.client.get(self.url, **self.extra)
            self.assertEqual(len(response.data['results']), len(objective))
            for i, res_objective in enumerate(response.data['results']):
                for field in ('description', 'metrics'):
                    self.assertEqual(res_objective[field]['storage_address'],
                                     objective[i][field]['storage_address'])

    def test_objective_retrieve_storage_addresses_update_with_cache(self):
        url = reverse('substrapp:objective-detail', args=[objective[0]['key']])
        o_objective = copy.deepcopy(objective[0])
        for field in ('description', 'metrics'):
            o_objective[field]['storage_address'] = \
                o_objective[field]['storage_address'].replace('http://testserver',
                                                              'http://remotetestserver')

        with mock.patch.object(OrchestratorClient, 'query_objective', return_value=o_objective), \
                mock.patch('substrapp.views.objective.node_has_process_permission',
                           return_value=True), \
                mock.patch('substrapp.views.objective.get_remote_asset', return_value=b'dummy binary content'):
            response = self.client.get(url, **self.extra)
            for field in ('description', 'metrics'):
                self.assertEqual(response.data[field]['storage_address'],
                                 objective[0][field]['storage_address'])

    def test_objective_retrieve_storage_addresses_update_without_cache(self):
        url = reverse('substrapp:objective-detail', args=[objective[0]['key']])
        o_objective = copy.deepcopy(objective[0])
        for field in ('description', 'metrics'):
            o_objective[field]['storage_address'] = \
                o_objective[field]['storage_address'].replace('http://testserver',
                                                              'http://remotetestserver')

        with mock.patch.object(OrchestratorClient, 'query_objective', return_value=o_objective), \
                mock.patch('substrapp.views.objective.node_has_process_permission',
                           return_value=False), \
                mock.patch('substrapp.views.objective.get_remote_asset', return_value=b'dummy binary content'):
            response = self.client.get(url, **self.extra)
            for field in ('description', 'metrics'):
                self.assertEqual(response.data[field]['storage_address'],
                                 objective[0][field]['storage_address'])

    @parameterized.expand([
        ("one_page_test", 2, 1, 0, 2),
        ("one_element_per_page_page_two", 1, 2, 1, 2),
    ])
    def test_objective_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        url = reverse('substrapp:objective-list')
        url = f"{url}?page_size={page_size}&page={page_number}"
        with mock.patch.object(OrchestratorClient, 'query_objectives', return_value=objective):
            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertContains(response, 'count', 1)
            self.assertContains(response, 'next', 1)
            self.assertContains(response, 'previous', 1)
            self.assertContains(response, 'results', 1)
            self.assertEqual(r['results'], objective[index_down:index_up])

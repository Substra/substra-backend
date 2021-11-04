import copy
import os
import shutil
import logging
import json

import mock
from parameterized import parameterized

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase


from orchestrator.client import OrchestratorClient
from grpc import RpcError, StatusCode

from ..common import get_sample_algo, AuthenticatedClient, encode_filter
from .. import assets

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT,
                   LEDGER_CHANNELS={'mychannel': {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}})
class AlgoViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.algo, self.algo_filename = get_sample_algo()

        self.extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }
        self.logger = logging.getLogger('django.request')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)
        self.url = reverse('substrapp:algo-list')

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    def test_algo_list_empty(self):
        with mock.patch.object(OrchestratorClient, 'query_algos', return_value=[]):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 0, 'next': None, 'previous': None, 'results': []})

    def test_algo_list_success(self):
        algos = assets.get_algos()
        algos_response = copy.deepcopy(algos)
        with mock.patch.object(OrchestratorClient, 'query_algos', return_value=algos_response):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': len(algos), 'next': None, 'previous': None, 'results': algos})

    def test_algo_list_filter_fail(self):
        with mock.patch.object(OrchestratorClient, 'query_algos', return_value=assets.get_algos()):
            search_params = '?search=algERRORo'
            response = self.client.get(self.url + search_params, **self.extra)
            self.assertIn('Malformed search filters', response.json()['message'])

    def test_algo_list_filter_name(self):
        algos = assets.get_algos()
        name_to_filter = encode_filter(algos[0]['name'])
        with mock.patch.object(OrchestratorClient, 'query_algos', return_value=algos):
            search_params = f'?search=algo%253Aname%253A{name_to_filter}'
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 1)
            self.assertEqual(r['count'], 1)

    def test_algo_list_filter_dual(self):
        algos_response = assets.get_algos()
        with mock.patch.object(OrchestratorClient, 'query_algos', return_value=algos_response):
            search_params = f'?search=algo%253Aname%253A{encode_filter(algos_response[2]["name"])}'
            search_params += f'%2Calgo%253Aowner%253A{encode_filter(algos_response[2]["owner"])}'
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 1)

    def test_algo_retrieve(self):
        algo = assets.get_algo()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        algo_response = copy.deepcopy(algo)

        with open(os.path.join(dir_path,
                               '../../../../fixtures/chunantes/algos/algo4/description.md'), 'rb') as f:
            content = f.read()

        with mock.patch.object(OrchestratorClient, 'query_algo', return_value=algo_response), \
                mock.patch('substrapp.views.algo.get_remote_asset', return_value=content):

            response = self.client.get(f'{self.url}{algo["key"]}/', **self.extra)
            self.assertEqual(response.json(), algo_response)

    def test_algo_retrieve_fail(self):
        algo = assets.get_algo()

        # Key not enough chars
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

        with mock.patch.object(OrchestratorClient, 'query_algo', side_effect=error):
            response = self.client.get(f'{self.url}{algo["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_algo_create(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        algo_path = os.path.join(dir_path, '../../../../fixtures/chunantes/algos/algo3/algo.tar.gz')
        description_path = os.path.join(dir_path, '../../../../fixtures/chunantes/algos/algo3/description.md')

        data = {
            'json': json.dumps({
                'name': 'Logistic regression',
                'metric_key': 'some key',
                'category': 'ALGO_SIMPLE',
                'permissions': {
                    'public': True,
                    'authorized_ids': [],
                },
            }),
            'file': open(algo_path, 'rb'),
            'description': open(description_path, 'rb'),
        }

        with mock.patch.object(OrchestratorClient, 'register_algo', return_value={}):
            response = self.client.post(self.url, data=data, format='multipart', **self.extra)
        self.assertIsNotNone(response.data['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data['description'].close()
        data['file'].close()

    def test_algo_list_storage_addresses_update(self):
        # mock content
        algos = assets.get_algos()
        algos_response = copy.deepcopy(algos)
        for o_algo in algos_response:
            for field in ('description', 'algorithm'):
                o_algo[field]['storage_address'] = \
                    o_algo[field]['storage_address'].replace('http://testserver',
                                                             'http://remotetestserver')
        with mock.patch.object(OrchestratorClient, 'query_algos', return_value=algos_response), \
                mock.patch('substrapp.views.algo.get_remote_asset', return_value=b'dummy binary content'):
            response = self.client.get(self.url, **self.extra)
            self.assertEqual(response.data['count'], len(algos))
            for i, res_algo in enumerate(response.data['results']):
                for field in ('description', 'algorithm'):
                    self.assertEqual(res_algo[field]['storage_address'],
                                     algos[i][field]['storage_address'])

    def test_algo_retrieve_storage_addresses_update_with_cache(self):
        algo = assets.get_algo()
        algo_response = copy.deepcopy(algo)
        url = reverse('substrapp:algo-detail', args=[algo['key']])
        for field in ('description', 'algorithm'):
            algo_response[field]['storage_address'] = \
                algo_response[field]['storage_address'].replace('http://testserver', 'http://remotetestserver')
        with mock.patch.object(OrchestratorClient, 'query_algo', return_value=algo_response), \
                mock.patch('substrapp.views.algo.node_has_process_permission',
                           return_value=True), \
                mock.patch('substrapp.views.algo.get_remote_asset', return_value=b'dummy binary content'):

            response = self.client.get(url, **self.extra)
            for field in ('description', 'algorithm'):
                self.assertEqual(response.data[field]['storage_address'],
                                 algo[field]['storage_address'])

    def test_algo_retrieve_storage_addresses_update_without_cache(self):
        algo = assets.get_algo()
        algo_response = copy.deepcopy(algo)
        url = reverse('substrapp:algo-detail', args=[algo['key']])

        for field in ('description', 'algorithm'):
            algo_response[field]['storage_address'] = \
                algo_response[field]['storage_address'].replace('http://testserver', 'http://remotetestserver')
        with mock.patch.object(OrchestratorClient, 'query_algo', return_value=algo_response), \
                mock.patch('substrapp.views.algo.node_has_process_permission',
                           return_value=False), \
                mock.patch('substrapp.views.algo.get_remote_asset', return_value=b'dummy binary content'):

            res = self.client.get(url, **self.extra)
            for field in ('description', 'algorithm'):
                self.assertEqual(res.data[field]['storage_address'],
                                 algo[field]['storage_address'])

    @parameterized.expand([
        ("one_page_test", 5, 1, 0, 5),
        ("one_element_per_page_page_two", 1, 2, 1, 2),
        ("two_element_per_page_page_three", 2, 3, 4, 6)
    ])
    def test_algo_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        algos = assets.get_algos()
        algos_response = copy.deepcopy(algos)
        url = reverse('substrapp:algo-list')
        url = f"{url}?page_size={page_size}&page={page_number}"
        with mock.patch.object(OrchestratorClient, 'query_algos', return_value=algos_response):
            response = self.client.get(url, **self.extra)
        r = response.json()
        self.assertContains(response, 'count', 1)
        self.assertContains(response, 'next', 1)
        self.assertContains(response, 'previous', 1)
        self.assertContains(response, 'results', 1)
        self.assertEqual(r['results'], algos[index_down:index_up])

import copy
import os
import shutil
import logging

import mock
from parameterized import parameterized

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from orchestrator.client import OrchestratorClient
from grpc import RpcError, StatusCode

from ..common import get_sample_datamanager, AuthenticatedClient, encode_filter
from ..assets import metric, datamanager

MEDIA_ROOT = "/tmp/unittests_views/"
CHANNEL = 'mychannel'
TEST_ORG = 'MyTestOrg'
MODEL_KEY = 'some-key'


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT,
                   LEDGER_CHANNELS={'mychannel': {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}},
                   LEDGER_MSP_ID=TEST_ORG)
class DataManagerViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.url = reverse('substrapp:data_manager-list')
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

    def test_datamanager_list_empty(self):
        with mock.patch.object(OrchestratorClient, 'query_datamanagers', return_value=[]):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 0, 'next': None, 'previous': None, 'results': []})

    def test_datamanager_list_success(self):
        with mock.patch.object(OrchestratorClient, 'query_datamanagers', return_value=datamanager):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r['results'], datamanager)

    def test_datamanager_list_filter_fail(self):
        with mock.patch.object(OrchestratorClient, 'query_datamanagers', return_value=datamanager):
            search_params = '?search=dataseERRORt'
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_datamanager_list_filter_name(self):
        name_to_filter = encode_filter(datamanager[-1]['name'])
        with mock.patch.object(OrchestratorClient, 'query_datamanagers', return_value=datamanager):
            search_params = f'?search=dataset%253Aname%253A{name_to_filter}'
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 1)

    def test_datamanager_retrieve(self):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'), 'rb') as f:
            opener_content = f.read()

        with open(os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                '../../../../fixtures/chunantes/datamanagers/datamanager0/description.md'), 'rb') as f:
            description_content = f.read()

        with mock.patch.object(OrchestratorClient, 'query_dataset', return_value=datamanager[0]), \
                mock.patch('substrapp.views.datamanager.get_remote_asset',
                           side_effect=[opener_content, description_content]):

            response = self.client.get(f'{self.url}{datamanager[0]["key"]}/', **self.extra)
            r = response.json()

            self.assertEqual(r, datamanager[0])

    def test_datamanager_retrieve_fail(self):

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

        with mock.patch.object(OrchestratorClient, 'query_dataset', side_effect=error):
            response = self.client.get(f'{self.url}{metric[0]["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_datamanager_list_storage_addresses_update(self):
        # mock content
        o_dms = copy.deepcopy(datamanager)
        for o_dm in o_dms:
            for field in ('description', 'opener'):
                o_dm[field]['storage_address'] = \
                    o_dm[field]['storage_address'] \
                    .replace('http://testserver', 'http://remotetestserver')
        with mock.patch.object(OrchestratorClient, 'query_datamanagers', return_value=o_dms), \
                mock.patch('substrapp.views.algo.get_remote_asset', return_value=b'dummy binary content'):
            response = self.client.get(self.url, **self.extra)
            self.assertEqual(response.data['count'], len(datamanager))
            for i, res_datamanager in enumerate(response.data['results']):
                for field in ('description', 'opener'):
                    self.assertEqual(res_datamanager[field]['storage_address'],
                                     datamanager[i][field]['storage_address'])

    def test_datamanager_retrieve_storage_addresses_update_with_cache(self):
        url = reverse('substrapp:data_manager-detail', args=[datamanager[0]['key']])

        o_dm = copy.deepcopy(datamanager[0])
        for field in ('description', 'opener'):
            o_dm[field]['storage_address'] = \
                o_dm[field]['storage_address'].replace('http://testserver',
                                                       'http://remotetestserver')
        with mock.patch.object(OrchestratorClient, 'query_dataset', return_value=o_dm), \
                mock.patch('substrapp.views.algo.node_has_process_permission',
                           return_value=True), \
                mock.patch('substrapp.views.datamanager.get_remote_asset', return_value=b'dummy binary content'):

            response = self.client.get(url, **self.extra)
            for field in ('description', 'opener'):
                self.assertEqual(response.data[field]['storage_address'],
                                 datamanager[0][field]['storage_address'])

    def test_datamanager_retrieve_storage_addresses_update_without_cache(self):
        url = reverse('substrapp:data_manager-detail', args=[datamanager[0]['key']])
        o_dm = copy.deepcopy(datamanager[0])
        for field in ('description', 'opener'):
            o_dm[field]['storage_address'] = \
                o_dm[field]['storage_address'].replace('http://testserver',
                                                       'http://remotetestserver')
        with mock.patch.object(OrchestratorClient, 'query_dataset', return_value=o_dm), \
                mock.patch('substrapp.views.algo.node_has_process_permission',
                           return_value=False), \
                mock.patch('substrapp.views.datamanager.get_remote_asset', return_value=b'dummy binary content'):

            response = self.client.get(url, **self.extra)
            for field in ('description', 'opener'):
                self.assertEqual(response.data[field]['storage_address'],
                                 datamanager[0][field]['storage_address'])

    @parameterized.expand([
        ("one_page_test", 2, 1, 0, 2),
        ("one_element_per_page_page_two", 1, 2, 1, 2),
    ])
    def test_data_manager_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        url = reverse('substrapp:data_manager-list')
        url = f"{url}?page_size={page_size}&page={page_number}"
        with mock.patch.object(OrchestratorClient, 'query_datamanagers', return_value=datamanager):
            response = self.client.get(url, **self.extra)
        r = response.json()
        self.assertContains(response, 'count', 1)
        self.assertContains(response, 'next', 1)
        self.assertContains(response, 'previous', 1)
        self.assertContains(response, 'results', 1)
        self.assertEqual(r['results'], datamanager[index_down:index_up])

import copy
import os
import shutil
import logging
import urllib

import mock

from parameterized import parameterized

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.views import ComputeTaskViewSet

from orchestrator.client import OrchestratorClient
from grpc import RpcError, StatusCode

from ..assets import traintuple, testtuple, metric
from ..common import AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


def get_compute_plan_key(assets):
    for asset in assets:
        compute_plan_key = asset.get('compute_plan_key')
        if compute_plan_key:
            return compute_plan_key
    raise Exception('Could not find a compute plan key')


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT,
                   LEDGER_CHANNELS={'mychannel': {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}})
class TraintupleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

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

    def test_traintuple_queryset(self):
        traintuple_view = ComputeTaskViewSet()
        self.assertFalse(traintuple_view.get_queryset())

    def test_traintuple_list_empty(self):
        url = reverse('substrapp:traintuple-list')

        with mock.patch.object(OrchestratorClient, 'query_tasks', return_value=[]):
            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 0, 'next': None, 'previous': None, 'results': []})

    def test_traintuple_retrieve(self):
        url = reverse('substrapp:traintuple-list')
        search_params = 'c164f4c7-14a7-8c7e-2ba2-016de231cdd4/'

        expected = copy.deepcopy(traintuple[0])
        expected['train']['models'] = None

        with mock.patch.object(OrchestratorClient, 'query_task', return_value=traintuple[0]), \
                mock.patch.object(OrchestratorClient, 'get_computetask_output_models', return_value=None):
            response = self.client.get(url + search_params, **self.extra)
            actual = response.json()
            self.assertEqual(actual, expected)

    def test_traintuple_retrieve_fail(self):

        url = reverse('substrapp:traintuple-list')

        # Key < 32 chars
        search_params = '12312323/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = 'X' * 32 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = RpcError()
        error.details = 'out of range test'
        error.code = lambda: StatusCode.OUT_OF_RANGE

        with mock.patch.object(OrchestratorClient, 'query_task', side_effect=error):
            response = self.client.get(f'{url}{metric[0]["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_traintuple_list_filter_tag(self):
        url = reverse('substrapp:traintuple-list')
        target_tag = 'foo'
        search_params = '?search=traintuple%253Atag%253A' + urllib.parse.quote_plus(target_tag)

        with mock.patch.object(OrchestratorClient, 'query_tasks', return_value=traintuple), \
                mock.patch.object(OrchestratorClient, 'get_computetask_output_models', return_value=None):
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 2)

    def test_traintuple_list_filter_compute_plan_key(self):
        url = reverse('substrapp:traintuple-list')
        compute_plan_key = get_compute_plan_key(traintuple)
        search_params = f'?search=traintuple%253Acompute_plan_key%253A{compute_plan_key}'

        with mock.patch.object(OrchestratorClient, 'query_tasks', return_value=traintuple), \
                mock.patch.object(OrchestratorClient, 'get_computetask_output_models', return_value=None):
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(len(r['results']), 1)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT,
                   LEDGER_CHANNELS={'mychannel': {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}})
class TesttupleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

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

    def test_testtuple_queryset(self):
        testtuple_view = ComputeTaskViewSet()
        self.assertFalse(testtuple_view.get_queryset())

    def test_testtuple_list_empty(self):
        url = reverse('substrapp:testtuple-list')
        with mock.patch.object(OrchestratorClient, 'query_tasks', return_value=[]):
            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 0, 'next': None, 'previous': None, 'results': []})

    def test_testtuple_retrieve(self):
        url = reverse('substrapp:testtuple-list')
        search_params = 'c164f4c7-14a7-8c7e-2ba2-016de231cdd4/'

        expected = copy.deepcopy(testtuple[0])
        expected['test']['perfs'] = {'key': 1}

        with mock.patch.object(OrchestratorClient, 'query_task', return_value=testtuple[0]), \
                mock.patch.object(OrchestratorClient, 'get_compute_task_performances',
                                  return_value=[{'metric_key': 'key', 'performance_value': 1}]):
            response = self.client.get(url + search_params, **self.extra)
            actual = response.json()
            self.assertEqual(actual, expected)

    def test_testtuple_retrieve_fail(self):

        url = reverse('substrapp:testtuple-list')

        # Key < 32 chars
        search_params = '12312323/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = 'X' * 32 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = RpcError()
        error.details = 'out of range test'
        error.code = lambda: StatusCode.OUT_OF_RANGE

        with mock.patch.object(OrchestratorClient, 'query_task', side_effect=error):
            response = self.client.get(f'{url}{metric[0]["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_testtuple_list_filter_tag(self):
        url = reverse('substrapp:testtuple-list')

        with mock.patch.object(OrchestratorClient, 'query_tasks', return_value=testtuple), \
                mock.patch.object(OrchestratorClient, 'get_compute_task_performances',
                                  return_value=[{'metric_key': 'key', 'performance_value': 1}]):
            search_params = '?search=testtuple%253Atag%253Abar'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(len(r['results']), 1)

            search_params = '?search=testtuple%253Atag%253Afoo'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 1)

    @parameterized.expand([
        ("one_page_test", 9, 1, 0, 9),
        ("one_element_per_page_page_two", 1, 2, 1, 2),
        ("two_element_per_page_page_two", 2, 2, 2, 4)
    ])
    def test_traintuple_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        url = reverse('substrapp:traintuple-list')
        url = f"{url}?page_size={page_size}&page={page_number}"
        with mock.patch.object(OrchestratorClient, 'query_tasks', return_value=traintuple), \
                mock.patch.object(OrchestratorClient, 'get_computetask_output_models', return_value=None):
            response = self.client.get(url, **self.extra)
        r = response.json()
        self.assertContains(response, 'count', 1)
        self.assertContains(response, 'next', 1)
        self.assertContains(response, 'previous', 1)
        self.assertContains(response, 'results', 1)
        self.assertEqual(r['results'], traintuple[index_down:index_up])

    @parameterized.expand([
        ("one_page_test", 5, 1, 0, 5),
        ("one_element_per_page_page_two", 1, 2, 1, 2),
        ("two_element_per_page_page_two", 2, 2, 2, 4)
    ])
    def test_testtuple_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        url = reverse('substrapp:testtuple-list')
        url = f"{url}?page_size={page_size}&page={page_number}"
        with mock.patch.object(OrchestratorClient, 'query_tasks', return_value=testtuple), \
                mock.patch.object(OrchestratorClient, 'get_compute_task_performances',
                                  return_value=[{'metric_key': 'key', 'performance_value': 1}]):
            response = self.client.get(url, **self.extra)
        r = response.json()
        self.assertContains(response, 'count', 1)
        self.assertContains(response, 'next', 1)
        self.assertContains(response, 'previous', 1)
        self.assertContains(response, 'results', 1)
        self.assertEqual(r['results'], testtuple[index_down:index_up])

import os
import shutil
import logging

import mock
from parameterized import parameterized

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.views import ComputeTaskViewSet

from orchestrator.client import OrchestratorClient
from grpc import RpcError, StatusCode

from ..assets import compositetraintuple, objective
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
class CompositeTraintupleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        self.url = reverse('substrapp:composite_traintuple-list')

        self.logger = logging.getLogger('django.request')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_compositetraintuple_queryset(self):
        compositetraintuple_view = ComputeTaskViewSet()
        self.assertFalse(compositetraintuple_view.get_queryset())

    def test_compositetraintuple_list_empty(self):
        with mock.patch.object(OrchestratorClient, 'query_tasks', return_value=[]):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 0, 'next': None, 'previous': None, 'results': []})

    def test_compositetraintuple_retrieve(self):

        with mock.patch.object(OrchestratorClient, 'query_task', return_value=compositetraintuple[0]), \
             mock.patch.object(OrchestratorClient, 'get_computetask_output_models', return_value=None):
            search_params = 'c164f4c7-14a7-8c7e-2ba2-016de231cdd4/'
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(r, compositetraintuple[0])

    def test_compositetraintuple_retrieve_fail(self):
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

        with mock.patch.object(OrchestratorClient, 'query_task', side_effect=error):
            response = self.client.get(f'{self.url}{objective[0]["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compositetraintuple_list_filter_tag(self):
        with mock.patch.object(OrchestratorClient, 'query_tasks', return_value=compositetraintuple), \
                mock.patch.object(OrchestratorClient, 'get_computetask_output_models', return_value=None):
            search_params = '?search=composite_traintuple%253Atag%253Asubstra'
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 1)

    @parameterized.expand([
        ("one_page_test", 8, 1, 0, 8),
        ("one_element_per_page_page_two", 1, 2, 1, 2),
        ("two_element_per_page_page_three", 2, 3, 4, 6)
    ])
    def test_composite_traintuple_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        url = reverse('substrapp:composite_traintuple-list')
        url = f"{url}?page_size={page_size}&page={page_number}"
        with mock.patch.object(OrchestratorClient, 'query_tasks', return_value=compositetraintuple), \
                mock.patch.object(OrchestratorClient, 'get_computetask_output_models', return_value=None):
            response = self.client.get(url, **self.extra)
        r = response.json()
        self.assertContains(response, 'count', 1)
        self.assertContains(response, 'next', 1)
        self.assertContains(response, 'previous', 1)
        self.assertContains(response, 'results', 1)
        self.assertEqual(r['results'], compositetraintuple[index_down:index_up])

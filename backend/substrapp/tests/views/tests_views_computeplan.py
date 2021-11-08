import copy
import os
import shutil
from grpc import RpcError, StatusCode
import mock
import urllib
import uuid

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from orchestrator.client import OrchestratorClient
from substrapp.views import ComputePlanViewSet

from ..common import AuthenticatedClient
from .. import common
from .. import assets

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT,
                   LEDGER_CHANNELS={'mychannel': {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}})
class ComputePlanViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        self.url = reverse('substrapp:compute_plan-list')

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_create(self):
        dummy_key = str(uuid.uuid4())

        data = {
            'traintuples': [{
                'algo_key': dummy_key,
                'data_manager_key': dummy_key,
                'train_data_sample_keys': [dummy_key],
                'traintuple_id': dummy_key,
            }],
            'testtuples': [{
                'traintuple_id': dummy_key,
                'metric_key': dummy_key,
                'data_manager_key': dummy_key,
            }]
        }

        with mock.patch.object(OrchestratorClient, 'register_compute_plan', return_value={}), \
                mock.patch.object(OrchestratorClient, 'register_tasks', return_value={}):
            response = self.client.post(self.url, data=data, format='json', **self.extra)
            self.assertEqual(response.json(), {})
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_without_tasks(self):
        data = {}

        with mock.patch.object(OrchestratorClient, 'register_compute_plan', return_value={}):
            response = self.client.post(self.url, data=data, format='json', **self.extra)
            self.assertEqual(response.json(), {})
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_computeplan_list_empty(self):
        with mock.patch.object(OrchestratorClient, 'query_compute_plans', return_value=[]):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 0, 'next': None, 'previous': None, 'results': []})

    def test_computeplan_list_success(self):
        cps = assets.get_compute_plans()
        cps_response = copy.deepcopy(cps)
        with mock.patch.object(OrchestratorClient, 'query_compute_plans', return_value=cps_response):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r['results'], cps)

    def test_computeplan_retrieve(self):
        cp = assets.get_compute_plan()
        cp_response = copy.deepcopy(cp)
        with mock.patch.object(OrchestratorClient, 'query_compute_plan', return_value=cp_response):
            url = reverse('substrapp:compute_plan-detail', args=[cp['key']])
            response = self.client.get(url, **self.extra)
            actual = response.json()
            self.assertEqual(actual, cp)

    def test_computeplan_retrieve_fail(self):
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

        cp = assets.get_compute_plan()

        with mock.patch.object(OrchestratorClient, 'query_compute_plan', side_effect=error):
            response = self.client.get(f'{self.url}{cp["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_computeplan_cancel(self):
        cp = assets.get_compute_plan()
        key = cp['key']
        with mock.patch.object(OrchestratorClient, 'cancel_compute_plan'), \
                mock.patch.object(OrchestratorClient, 'query_compute_plan', return_value=cp):
            url = reverse('substrapp:compute_plan-cancel', args=[key])
            response = self.client.post(url, **self.extra)
            r = response.json()
            self.assertEqual(r, cp)

    def test_parse_composite_traintuples(self):
        dummy_key = str(uuid.uuid4())
        dummy_key2 = str(uuid.uuid4())

        composite = [
            {
                "composite_traintuple_id": dummy_key,
                "in_head_model_id": dummy_key,
                "in_trunk_model_id": dummy_key2,
                "algo_key": dummy_key,
                "metadata": {
                    "simple_metadata": "data"
                },
                "data_manager_key": dummy_key,
                "train_data_sample_keys": [dummy_key, dummy_key],
                "out_trunk_model_permissions": {
                    "public": False,
                    "authorized_ids": ["test-org"]
                }
            }
        ]

        cp = ComputePlanViewSet()
        tasks = cp.parse_composite_traintuple(None, composite, dummy_key)

        self.assertEqual(len(tasks[dummy_key]["parent_task_keys"]), 2)

    def test_can_see_traintuple(self):

        cp = assets.get_compute_plan()
        cp_response = copy.deepcopy(cp)
        tasks = assets.get_train_tasks()[0:2]
        tasks_response = copy.deepcopy(tasks)

        url = reverse('substrapp:compute_plan_traintuple-list', args=[cp['key']])
        url = f"{url}?page_size=2"

        with mock.patch.object(OrchestratorClient, 'query_compute_plan', return_value=cp_response), \
                mock.patch.object(OrchestratorClient, 'query_tasks', return_value=tasks_response), \
                mock.patch.object(OrchestratorClient, 'get_computetask_output_models',
                                  side_effect=common.get_task_output_models), \
                mock.patch.object(OrchestratorClient, 'query_events', side_effect=common.get_task_events):

            response = self.client.get(url, **self.extra)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['results'], tasks[0:2])
        # # maybe add a test without ?page_size=<int> and add a forbidden response

    def test_can_filter_tuples(self):

        cp = assets.get_compute_plan()
        cp_response = copy.deepcopy(cp)

        url = reverse('substrapp:compute_plan_traintuple-list', args=[cp['key']])
        target_tag = 'foo'
        search_params = '?page_size=10&page=1&search=traintuple%253Atag%253A' + urllib.parse.quote_plus(target_tag)

        with mock.patch.object(OrchestratorClient, 'query_compute_plan', return_value=cp_response), \
                mock.patch.object(OrchestratorClient, 'query_tasks', return_value=assets.get_train_tasks()), \
                mock.patch.object(OrchestratorClient, 'get_computetask_output_models', return_value=None), \
                mock.patch.object(OrchestratorClient, 'query_events', side_effect=common.get_task_events):
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 2)

    def test_can_see_algos(self):
        cp = assets.get_compute_plan()
        cp_response = copy.deepcopy(cp)
        compute_plan_key = cp_response['key']
        algos = assets.get_algos()
        algos_response = copy.deepcopy(algos)

        url = reverse('substrapp:compute_plan_algo-list', args=[compute_plan_key])
        url = f"{url}?page_size=2"

        with mock.patch.object(OrchestratorClient, 'query_compute_plan', return_value=cp_response), \
                mock.patch.object(OrchestratorClient,
                                  'query_algos',
                                  return_value=[algos_response[0], algos_response[1]]):

            response = self.client.get(url, **self.extra)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['results'], algos_response[0:2])

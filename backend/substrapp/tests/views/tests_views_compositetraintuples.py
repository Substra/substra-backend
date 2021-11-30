import copy
import logging
import os
import shutil

import mock
from django.test import override_settings
from django.urls import reverse
from grpc import RpcError
from grpc import StatusCode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from orchestrator.client import OrchestratorClient
from substrapp.views import ComputeTaskViewSet

from .. import assets
from .. import common
from ..common import AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


def get_compute_plan_key(assets):
    for asset in assets:
        compute_plan_key = asset.get("compute_plan_key")
        if compute_plan_key:
            return compute_plan_key
    raise Exception("Could not find a compute plan key")


# APITestCase
@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
)
class CompositeTraintupleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        self.url = reverse("substrapp:composite_traintuple-list")

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_compositetraintuple_queryset(self):
        compositetraintuple_view = ComputeTaskViewSet()
        self.assertFalse(compositetraintuple_view.get_queryset())

    def test_compositetraintuple_list_empty(self):
        with mock.patch.object(OrchestratorClient, "query_tasks", return_value=[]):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r, {"count": 0, "next": None, "previous": None, "results": []})

    def test_compositetraintuple_retrieve(self):
        composite_task = assets.get_composite_task()

        parent_tasks = [
            t
            for t in (assets.get_train_tasks() + assets.get_composite_tasks())
            if t["key"] in composite_task["parent_task_keys"]
        ]
        data_manager = common.query_data_manager(composite_task["composite"]["data_manager_key"])

        expected = composite_task
        expected["composite"]["models"] = []
        expected["composite"]["data_manager"] = copy.deepcopy(data_manager)
        expected["parent_tasks"] = copy.deepcopy(parent_tasks)

        filtered_events = [iter([event]) for event in common.get_task_events(composite_task["key"])]

        with mock.patch.object(OrchestratorClient, "query_task", side_effect=common.query_task), mock.patch.object(
            OrchestratorClient, "query_datamanager", return_value=data_manager
        ), mock.patch.object(OrchestratorClient, "get_computetask_output_models", return_value=[]), mock.patch.object(
            OrchestratorClient, "query_events_generator", side_effect=filtered_events
        ):
            search_params = f"{composite_task['key']}/"
            response = self.client.get(self.url + search_params, **self.extra)
            actual = response.json()
            self.assertEqual(actual, expected)

    def test_compositetraintuple_retrieve_fail(self):
        # Key < 32 chars
        search_params = "12312323/"
        response = self.client.get(self.url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = "X" * 32 + "/"
        response = self.client.get(self.url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = RpcError()
        error.details = "out of range test"
        error.code = lambda: StatusCode.OUT_OF_RANGE

        metric = assets.get_metric()

        with mock.patch.object(OrchestratorClient, "query_task", side_effect=error):
            response = self.client.get(f'{self.url}{metric["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compositetraintuple_list_filter_tag(self):

        composite_tasks = assets.get_composite_tasks()
        filtered_events = [iter([event]) for ct in composite_tasks for event in common.get_task_events(ct["key"])]

        with mock.patch.object(OrchestratorClient, "query_tasks", return_value=composite_tasks), mock.patch.object(
            OrchestratorClient, "get_computetask_output_models", return_value=[]
        ), mock.patch.object(OrchestratorClient, "query_events_generator", side_effect=filtered_events):

            search_params = "?search=composite_traintuple%253Atag%253Asubstra"
            response = self.client.get(self.url + search_params, **self.extra)

            r = response.json()

            self.assertEqual(len(r["results"]), 1)

    @parameterized.expand(
        [
            ("one_page_test", 8, 1, 0, 8),
            ("one_element_per_page_page_two", 1, 2, 1, 2),
            ("two_element_per_page_page_three", 2, 3, 4, 6),
        ]
    )
    def test_composite_traintuple_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        composite_tasks = assets.get_composite_tasks()
        filtered_events = [iter([event]) for ct in composite_tasks for event in common.get_task_events(ct["key"])]

        url = reverse("substrapp:composite_traintuple-list")
        url = f"{url}?page_size={page_size}&page={page_number}"
        with mock.patch.object(
            OrchestratorClient, "query_tasks", return_value=assets.get_composite_tasks()
        ), mock.patch.object(
            OrchestratorClient, "get_computetask_output_models", side_effect=common.get_task_output_models
        ), mock.patch.object(
            OrchestratorClient, "query_events_generator", side_effect=filtered_events
        ):
            response = self.client.get(url, **self.extra)
        r = response.json()
        self.assertContains(response, "count", 1)
        self.assertContains(response, "next", 1)
        self.assertContains(response, "previous", 1)
        self.assertContains(response, "results", 1)
        self.assertEqual(r["results"], composite_tasks[index_down:index_up])

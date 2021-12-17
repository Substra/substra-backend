import copy
import logging
import os
import shutil
import tempfile
import urllib
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from grpc import StatusCode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

import orchestrator.error
from orchestrator.client import OrchestratorClient
from substrapp.views import ComputeTaskViewSet

from .. import assets
from .. import common
from ..common import AuthenticatedClient
from ..common import internal_server_error_on_exception

MEDIA_ROOT = tempfile.mkdtemp()


def get_compute_plan_key(assets):
    for asset in assets:
        compute_plan_key = asset.get("compute_plan_key")
        if compute_plan_key:
            return compute_plan_key
    raise Exception("Could not find a compute plan key")


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class TraintupleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    @internal_server_error_on_exception()
    @mock.patch.object(ComputeTaskViewSet, "commit", side_effect=Exception("Unexpected error"))
    def test_traintuple_create_fail_internal_server_error(self, commit: mock.Mock):
        url = reverse("substrapp:traintuple-list")
        response = self.client.post(url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        commit.assert_called_once()

    def test_traintuple_queryset(self):
        traintuple_view = ComputeTaskViewSet()
        self.assertFalse(traintuple_view.get_queryset())

    def test_traintuple_list_empty(self):
        url = reverse("substrapp:traintuple-list")

        with mock.patch.object(OrchestratorClient, "query_tasks", return_value=[]):
            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, {"count": 0, "next": None, "previous": None, "results": []})

    def test_traintuple_retrieve(self):
        url = reverse("substrapp:traintuple-list")
        search_params = "c164f4c7-14a7-8c7e-2ba2-016de231cdd4/"

        task = assets.get_train_task()
        filtered_events = [iter([event]) for event in common.get_task_events(task["key"])]

        data_manager = assets.get_data_manager()

        expected = copy.deepcopy(task)
        expected["train"]["models"] = None
        expected["train"]["data_manager"] = data_manager
        expected["parent_tasks"] = []
        expected["error_type"] = None

        with mock.patch.object(OrchestratorClient, "query_task", return_value=task), mock.patch.object(
            OrchestratorClient, "query_datamanager", return_value=data_manager
        ), mock.patch.object(OrchestratorClient, "get_computetask_output_models", return_value=None), mock.patch.object(
            OrchestratorClient, "get_computetask_output_models", return_value=None
        ), mock.patch.object(
            OrchestratorClient, "query_events_generator", side_effect=filtered_events
        ), mock.patch(
            "substrapp.views.utils._get_error_type", return_value=None
        ) as mocked_get_error_type:

            response = self.client.get(url + search_params, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            actual = response.json()
            self.assertEqual(actual, expected)
            mocked_get_error_type.assert_called_once()

    def test_traintuple_retrieve_fail(self):

        url = reverse("substrapp:traintuple-list")

        # Key < 32 chars
        search_params = "12312323/"
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = "X" * 32 + "/"
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = orchestrator.error.OrcError()
        error.details = "out of range test"
        error.code = StatusCode.OUT_OF_RANGE

        metric = assets.get_metric()

        with mock.patch.object(OrchestratorClient, "query_task", side_effect=error):
            response = self.client.get(f'{url}{metric["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @internal_server_error_on_exception()
    @mock.patch.object(ComputeTaskViewSet, "_retrieve", side_effect=Exception("Unexpected error"))
    def test_testtuple_retrieve_fail_internal_server_error(self, _retrieve: mock.Mock):
        url = reverse("substrapp:traintuple-detail", kwargs={"pk": 123})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        _retrieve.assert_called_once()

    def test_traintuple_list_filter_tag(self):
        url = reverse("substrapp:traintuple-list")
        target_tag = "foo"
        search_params = "?search=traintuple%253Atag%253A" + urllib.parse.quote_plus(target_tag)

        tasks = assets.get_train_tasks()
        filtered_events = [iter([event]) for t in tasks for event in common.get_task_events(t["key"])]

        with mock.patch.object(OrchestratorClient, "query_tasks", return_value=tasks), mock.patch.object(
            OrchestratorClient, "get_computetask_output_models", return_value=None
        ), mock.patch.object(OrchestratorClient, "query_events_generator", side_effect=filtered_events), mock.patch(
            "substrapp.views.utils._get_error_type", return_value=None
        ) as mocked_get_error_type:
            response = self.client.get(url + search_params, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            r = response.json()
            self.assertEqual(len(r["results"]), 2)
            self.assertEqual(mocked_get_error_type.call_count, 2)

    def test_traintuple_list_filter_compute_plan_key(self):

        tasks = assets.get_train_tasks()
        filtered_events = [iter([event]) for t in tasks for event in common.get_task_events(t["key"])]
        url = reverse("substrapp:traintuple-list")
        compute_plan_key = get_compute_plan_key(tasks)
        search_params = f"?search=traintuple%253Acompute_plan_key%253A{compute_plan_key}"

        with mock.patch.object(OrchestratorClient, "query_tasks", return_value=tasks), mock.patch.object(
            OrchestratorClient, "get_computetask_output_models", return_value=None
        ), mock.patch.object(OrchestratorClient, "query_events_generator", side_effect=filtered_events), mock.patch(
            "substrapp.views.utils._get_error_type", return_value=None
        ) as mocked_get_error_type:

            response = self.client.get(url + search_params, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            r = response.json()
            self.assertEqual(len(r["results"]), 1)
            mocked_get_error_type.assert_called_once()

    @internal_server_error_on_exception()
    @mock.patch.object(ComputeTaskViewSet, "_retrieve", side_effect=Exception("Unexpected error"))
    def test_traintuple_retrieve_fail_internal_server_error(self, _retrieve: mock.Mock):
        url = reverse("substrapp:traintuple-detail", args={"pk": 123})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        _retrieve.assert_called_once()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class TesttupleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    @internal_server_error_on_exception()
    @mock.patch.object(ComputeTaskViewSet, "commit", side_effect=Exception("Unexpected error"))
    def test_testtuple_create_fail_internal_server_error(self, commit: mock.Mock):
        url = reverse("substrapp:testtuple-list")
        response = self.client.post(url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        commit.assert_called_once()

    def test_testtuple_queryset(self):
        testtuple_view = ComputeTaskViewSet()
        self.assertFalse(testtuple_view.get_queryset())

    def test_testtuple_list_empty(self):
        url = reverse("substrapp:testtuple-list")
        with mock.patch.object(OrchestratorClient, "query_tasks", return_value=[]):
            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, {"count": 0, "next": None, "previous": None, "results": []})

    def test_testtuple_retrieve(self):

        test_task = assets.get_test_task()

        parent_tasks = [
            t
            for t in (assets.get_train_tasks() + assets.get_composite_tasks())
            if t["key"] in test_task["parent_task_keys"]
        ]
        filtered_events = [
            iter([event]) for t in [test_task] + parent_tasks for event in common.get_task_events(t["key"])
        ]

        data_manager = common.query_data_manager(test_task["test"]["data_manager_key"])
        metrics = [m for m in assets.get_metrics() if m["key"] in test_task["test"]["metric_keys"]]
        metric = metrics[0]
        performances = common.get_task_performances(test_task["key"])

        url = reverse("substrapp:testtuple-list")
        search_params = f'{test_task["key"]}/'

        expected = copy.deepcopy(test_task)
        expected["parent_tasks"] = copy.deepcopy(parent_tasks)
        expected["test"]["data_manager"] = copy.deepcopy(data_manager)
        expected["test"]["metrics"] = copy.deepcopy(metrics)
        expected["test"]["perfs"] = {
            performance["metric_key"]: performance["performance_value"] for performance in performances
        }
        expected["error_type"] = None

        with mock.patch.object(OrchestratorClient, "query_task", side_effect=common.query_task), mock.patch.object(
            OrchestratorClient, "query_datamanager", return_value=data_manager
        ), mock.patch.object(OrchestratorClient, "query_metric", return_value=metric), mock.patch.object(
            OrchestratorClient, "get_compute_task_performances", return_value=performances
        ), mock.patch.object(
            OrchestratorClient, "query_events_generator", side_effect=filtered_events
        ), mock.patch(
            "substrapp.views.utils._get_error_type", return_value=None
        ) as mocked_get_error_type:
            response = self.client.get(url + search_params, **self.extra)
            actual = response.json()
            self.assertEqual(actual, expected)
            mocked_get_error_type.assert_called_once()

    def test_testtuple_retrieve_fail(self):

        url = reverse("substrapp:testtuple-list")

        # Key < 32 chars
        search_params = "12312323/"
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = "X" * 32 + "/"
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = orchestrator.error.OrcError()
        error.details = "out of range test"
        error.code = StatusCode.OUT_OF_RANGE

        metric = assets.get_metric()

        with mock.patch.object(OrchestratorClient, "query_task", side_effect=error):
            response = self.client.get(f'{url}{metric["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @internal_server_error_on_exception()
    @mock.patch.object(ComputeTaskViewSet, "_retrieve", side_effect=Exception("Unexpected error"))
    def test_testtuple_retrieve_fail_internal_server_error(self, _retrieve: mock.Mock):
        url = reverse("substrapp:testtuple-detail", kwargs={"pk": 123})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        _retrieve.assert_called_once()

    def test_testtuple_list_filter_tag(self):
        url = reverse("substrapp:testtuple-list")

        tasks = assets.get_test_tasks()
        filtered_events = [iter([event]) for t in tasks for event in common.get_task_events(t["key"])]

        with mock.patch.object(OrchestratorClient, "query_tasks", return_value=tasks), mock.patch.object(
            OrchestratorClient, "get_compute_task_performances", side_effect=common.get_task_performances
        ), mock.patch("substrapp.views.utils._get_error_type", return_value=None) as mocked_get_error_type:

            with mock.patch.object(OrchestratorClient, "query_events_generator", side_effect=filtered_events):
                search_params = "?search=testtuple%253Atag%253Abar"
                response = self.client.get(url + search_params, **self.extra)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                r = response.json()
                self.assertEqual(len(r["results"]), 1)

            with mock.patch.object(OrchestratorClient, "query_events_generator", side_effect=filtered_events):
                search_params = "?search=testtuple%253Atag%253Afoo"
                response = self.client.get(url + search_params, **self.extra)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                r = response.json()
                self.assertEqual(len(r["results"]), 1)

            mocked_get_error_type.assert_called_once()

    @parameterized.expand(
        [
            ("one_page_test", 9, 1, 0, 9),
            ("one_element_per_page_page_two", 1, 2, 1, 2),
            ("two_element_per_page_page_two", 2, 2, 2, 4),
        ]
    )
    def test_traintuple_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        train_tasks = assets.get_train_tasks()
        filtered_events = [iter([event]) for t in train_tasks for event in common.get_task_events(t["key"])]

        expected = copy.deepcopy(train_tasks)
        for task in expected:
            task["error_type"] = None

        url = reverse("substrapp:traintuple-list")
        url = f"{url}?page_size={page_size}&page={page_number}"

        with mock.patch.object(OrchestratorClient, "query_tasks", return_value=train_tasks), mock.patch.object(
            OrchestratorClient, "get_computetask_output_models", side_effect=common.get_task_output_models
        ), mock.patch.object(OrchestratorClient, "query_events_generator", side_effect=filtered_events), mock.patch(
            "substrapp.views.utils._get_error_type", return_value=None
        ) as mocked_get_error_type:
            response = self.client.get(url, **self.extra)
        r = response.json()
        self.assertContains(response, "count", 1)
        self.assertContains(response, "next", 1)
        self.assertContains(response, "previous", 1)
        self.assertContains(response, "results", 1)
        self.assertEqual(r["results"], expected[index_down:index_up])
        mocked_get_error_type.assert_called()

    @parameterized.expand(
        [
            ("one_page_test", 5, 1, 0, 5),
            ("one_element_per_page_page_two", 1, 2, 1, 2),
            ("two_element_per_page_page_two", 2, 2, 2, 4),
        ]
    )
    def test_testtuple_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        test_tasks = assets.get_test_tasks()
        filtered_events = [iter([event]) for t in test_tasks for event in common.get_task_events(t["key"])]

        expected = copy.deepcopy(test_tasks)
        for task in expected:
            task["error_type"] = None

        url = reverse("substrapp:testtuple-list")
        url = f"{url}?page_size={page_size}&page={page_number}"

        with mock.patch.object(OrchestratorClient, "query_tasks", return_value=test_tasks), mock.patch.object(
            OrchestratorClient, "get_compute_task_performances", side_effect=common.get_task_performances
        ), mock.patch.object(OrchestratorClient, "query_events_generator", side_effect=filtered_events), mock.patch(
            "substrapp.views.utils._get_error_type", return_value=None
        ) as mocked_get_error_type:
            response = self.client.get(url, **self.extra)
        r = response.json()
        self.assertContains(response, "count", 1)
        self.assertContains(response, "next", 1)
        self.assertContains(response, "previous", 1)
        self.assertContains(response, "results", 1)
        self.assertEqual(r["results"], expected[index_down:index_up])
        mocked_get_error_type.assert_called()

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computetask.get_channel_name", side_effect=Exception("Unexpected error"))
    def test_list_fail_internal_server_error(self, get_channel_name: mock.Mock):
        url = reverse("substrapp:testtuple-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        get_channel_name.assert_called_once()

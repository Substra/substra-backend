import copy
import os
import shutil
import tempfile
import uuid
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APITestCase

import orchestrator.computeplan_pb2 as computeplan_pb2
from localrep.models import ComputePlan as ComputePlanRep
from localrep.serializers import AlgoSerializer as AlgoRepSerializer
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from orchestrator.client import OrchestratorClient
from substrapp.views import ComputePlanViewSet
from substrapp.views import CPAlgoViewSet
from substrapp.views import CPTaskViewSet

from .. import assets
from .. import common
from ..common import AuthenticatedClient
from ..common import internal_server_error_on_exception

MEDIA_ROOT = tempfile.mkdtemp()


def mock_register_compute_plan(data):
    """Build orchestrator register response from request data."""
    return {
        "key": data["key"],
        "tag": data["tag"],
        "metadata": data["metadata"],
        "delete_intermediary_models": data["delete_intermediary_models"],
        "status": computeplan_pb2.ComputePlanStatus.Name(computeplan_pb2.PLAN_STATUS_TODO),
        "task_count": 0,
        "done_count": 0,
        "waiting_count": 0,
        "todo_count": 0,
        "doing_count": 0,
        "canceled_count": 0,
        "failed_count": 0,
        "owner": "MyOrg1MSP",
        "creation_date": "2021-11-04T13:54:09.882662Z",
    }


class AuthenticatedAPITestCase(APITestCase):
    client_class = AuthenticatedClient


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={
        "mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True},
        "yourchannel": {"chaincode": {"name": "yourcc"}, "model_export_enabled": True},
    },
)
class ComputePlanViewTests(AuthenticatedAPITestCase):
    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        self.url = reverse("substrapp:compute_plan-list")

        self.compute_plans = assets.get_compute_plans()
        self.query_compute_plans_index = {}
        for compute_plan in self.compute_plans:
            serializer = ComputePlanRepSerializer(data={"channel": "mychannel", **compute_plan})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            self.query_compute_plans_index[compute_plan["key"]] = compute_plan

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_create(self):
        dummy_key = str(uuid.uuid4())

        data = {
            "tag": "foo",
            "traintuples": [
                {
                    "algo_key": dummy_key,
                    "data_manager_key": dummy_key,
                    "train_data_sample_keys": [dummy_key],
                    "traintuple_id": dummy_key,
                }
            ],
            "testtuples": [
                {
                    "traintuple_id": dummy_key,
                    "metric_key": dummy_key,
                    "data_manager_key": dummy_key,
                }
            ],
        }

        with mock.patch.object(
            OrchestratorClient, "register_compute_plan", side_effect=mock_register_compute_plan
        ), mock.patch.object(OrchestratorClient, "register_tasks", return_value={}):
            response = self.client.post(self.url, data=data, format="json", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data["key"])
        # asset created in local db
        self.assertEqual(ComputePlanRep.objects.count(), len(self.compute_plans) + 1)

    def test_create_without_tasks(self):
        data = {"tag": "foo"}

        with mock.patch.object(OrchestratorClient, "register_compute_plan", side_effect=mock_register_compute_plan):
            response = self.client.post(self.url, data=data, format="json", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data["key"])
        # asset created in local db
        self.assertEqual(ComputePlanRep.objects.count(), len(self.compute_plans) + 1)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computeplan.ComputePlanViewSet.create", side_effect=Exception("Unexpected error"))
    def test_computeplan_create_fail_internal_server_error(self, _):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_computeplan_list_empty(self):
        ComputePlanRep.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def mock_query_compute_plan(self, key):
        return self.query_compute_plans_index[key]

    def mock_cp_failed_task(self, _, data):
        compute_plan = self.query_compute_plans_index[data["key"]]
        data["failed_task"] = compute_plan["failed_task"]
        return data

    def mock_cp_duration(self, _, data):
        compute_plan = self.query_compute_plans_index[data["key"]]
        data["start_date"] = compute_plan["start_date"]
        data["end_date"] = compute_plan["end_date"]
        data["estimated_end_date"] = compute_plan["estimated_end_date"]
        data["duration"] = compute_plan["duration"]
        return data

    def test_computeplan_list_success(self):
        self.maxDiff = None
        with mock.patch.object(
            OrchestratorClient, "query_compute_plan", side_effect=self.mock_query_compute_plan
        ), mock.patch(
            "substrapp.views.computeplan.add_compute_plan_duration_or_eta", side_effect=self.mock_cp_duration
        ):
            response = self.client.get(self.url, **self.extra)
        for compute_plan in self.compute_plans:
            del compute_plan["failed_task"]
        self.assertEqual(
            response.json(),
            {"count": len(self.compute_plans), "next": None, "previous": None, "results": self.compute_plans},
        )

    def test_computeplan_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computeplan.ComputePlanViewSet.list", side_effect=Exception("Unexpected error"))
    def test_computeplan_list_fail_internal_server_error(self, _):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_computeplan_retrieve(self):
        url = reverse("substrapp:compute_plan-detail", args=[self.compute_plans[0]["key"]])
        with mock.patch.object(
            OrchestratorClient, "query_compute_plan", side_effect=self.mock_query_compute_plan
        ), mock.patch(
            "substrapp.views.computeplan.add_compute_plan_failed_task", side_effect=self.mock_cp_failed_task
        ), mock.patch(
            "substrapp.views.computeplan.add_compute_plan_duration_or_eta", side_effect=self.mock_cp_duration
        ):
            response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.compute_plans[0])

    def test_computeplan_retrieve_fail(self):
        # Key < 32 chars
        url = reverse("substrapp:compute_plan-detail", args=["12312323"])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        url = reverse("substrapp:compute_plan-detail", args=["X" * 32])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computeplan.ComputePlanViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_computeplan_retrieve_fail_internal_server_error(self, _):
        url = reverse("substrapp:compute_plan-detail", args=[self.compute_plans[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_computeplan_cancel(self):
        url = reverse("substrapp:compute_plan-cancel", args=[self.compute_plans[0]["key"]])
        with mock.patch.object(OrchestratorClient, "cancel_compute_plan"), mock.patch.object(
            OrchestratorClient, "query_compute_plan", return_value=self.compute_plans[0]
        ):
            response = self.client.post(url, **self.extra)
        self.assertEqual(response.json(), self.compute_plans[0])

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computeplan.ComputePlanViewSet.cancel", side_effect=Exception("Unexpected error"))
    def test_computeplan_cancel_fail_internal_server_error(self, _):
        url = reverse("substrapp:compute_plan-cancel", args=[self.compute_plans[0]["key"]])
        response = self.client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_parse_composite_traintuples(self):
        dummy_key = str(uuid.uuid4())
        dummy_key2 = str(uuid.uuid4())

        composite = [
            {
                "composite_traintuple_id": dummy_key,
                "in_head_model_id": dummy_key,
                "in_trunk_model_id": dummy_key2,
                "algo_key": dummy_key,
                "metadata": {"simple_metadata": "data"},
                "data_manager_key": dummy_key,
                "train_data_sample_keys": [dummy_key, dummy_key],
                "out_trunk_model_permissions": {"public": False, "authorized_ids": ["test-org"]},
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
        filtered_events = [iter([event]) for tr in tasks_response for event in common.get_task_events(tr["key"])]

        url = reverse("substrapp:compute_plan_traintuple-list", args=[cp["key"]])
        url = f"{url}?page_size=2"

        with mock.patch.object(OrchestratorClient, "query_compute_plan", return_value=cp_response), mock.patch.object(
            OrchestratorClient, "query_tasks", return_value=tasks_response
        ), mock.patch.object(
            OrchestratorClient, "get_computetask_output_models", side_effect=common.get_task_output_models
        ), mock.patch.object(
            OrchestratorClient, "query_events_generator", side_effect=filtered_events
        ), mock.patch(
            "substrapp.views.utils._get_error_type", return_value=None
        ) as mocked_get_error_type:

            response = self.client.get(url, **self.extra)
            self.assertEqual(mocked_get_error_type.call_count, 2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected = [{**t, "error_type": None} for t in tasks[0:2]]
        self.assertEqual(response.json()["results"], expected)
        # # maybe add a test without ?page_size=<int> and add a forbidden response

    def test_can_filter_tuples(self):
        tasks_response = assets.get_train_tasks()
        filtered_events = [iter([event]) for tr in tasks_response for event in common.get_task_events(tr["key"])]

        url = reverse("substrapp:compute_plan_traintuple-list", args=[self.compute_plans[0]["key"]])
        params = urlencode({"page_size": 10, "page": 1, "search": "traintuple:tag:foo"})

        with mock.patch.object(
            OrchestratorClient, "query_compute_plan", return_value=self.compute_plans[0]
        ), mock.patch.object(OrchestratorClient, "query_tasks", return_value=tasks_response), mock.patch.object(
            OrchestratorClient, "get_computetask_output_models", return_value=None
        ), mock.patch.object(
            OrchestratorClient, "query_events_generator", side_effect=filtered_events
        ), mock.patch(
            "substrapp.views.utils._get_error_type", return_value=None
        ) as mocked_get_error_type:

            response = self.client.get(f"{url}?{params}", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            r = response.json()
            self.assertEqual(len(r["results"]), 2)
            self.assertEqual(mocked_get_error_type.call_count, 2)

    def test_can_see_algos(self):
        algos = assets.get_algos()
        for algo in algos:
            serializer = AlgoRepSerializer(data={"channel": "mychannel", **algo})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        url = reverse("substrapp:compute_plan_algo-list", args=[self.compute_plans[0]["key"]])
        params = urlencode({"page_size": 2})
        with mock.patch.object(OrchestratorClient, "query_algos", return_value=algos):
            response = self.client.get(f"{url}?{params}", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["results"], algos[0:2])

    @internal_server_error_on_exception()
    @mock.patch(
        "substrapp.views.computeplan.ComputePlanViewSet.update_ledger", side_effect=Exception("Unexpected error")
    )
    def test_computeplan_update_ledger_fail_internal_server_error(self, _):
        url = reverse("substrapp:compute_plan-update-ledger", kwargs={"pk": self.compute_plans[0]["key"]})
        response = self.client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class CPTaskViewSetTests(AuthenticatedAPITestCase):
    @internal_server_error_on_exception()
    @mock.patch.object(CPTaskViewSet, "is_page_size_param_present", side_effect=Exception("Unexpected error"))
    def test_list_fail_internal_server_error(self, validate_key: mock.Mock):
        url = reverse("substrapp:compute_plan_composite_traintuple-list", kwargs={"compute_plan_pk": 123})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        validate_key.assert_called_once()


class CPAlgoViewSetTests(AuthenticatedAPITestCase):
    @internal_server_error_on_exception()
    @mock.patch.object(CPAlgoViewSet, "is_page_size_param_present", side_effect=Exception("Unexpected error"))
    def test_list_fail_internal_server_error(self, validate_key: mock.Mock):
        url = reverse("substrapp:compute_plan_algo-list", kwargs={"compute_plan_pk": 123})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        validate_key.assert_called_once()

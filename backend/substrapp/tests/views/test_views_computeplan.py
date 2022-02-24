import os
import shutil
import tempfile
import uuid
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.failure_report_pb2 as failure_report_pb2
from localrep.models import ComputePlan as ComputePlanRep
from localrep.serializers import AlgoSerializer as AlgoRepSerializer
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from localrep.serializers import DataManagerSerializer as DataManagerRepSerializer
from localrep.serializers import DataSampleSerializer as DataSampleRepSerializer
from localrep.serializers import MetricSerializer as MetricRepSerializer
from orchestrator.client import OrchestratorClient
from substrapp.compute_tasks.errors import ComputeTaskErrorType
from substrapp.views import ComputePlanViewSet

from .. import assets
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

        self.algos = assets.get_algos()
        for algo in self.algos:
            serializer = AlgoRepSerializer(data={"channel": "mychannel", **algo})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.metrics = assets.get_metrics()
        for metric in self.metrics:
            serializer = MetricRepSerializer(data={"channel": "mychannel", **metric})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.data_managers = assets.get_data_managers()
        for data_manager in self.data_managers:
            serializer = DataManagerRepSerializer(data={"channel": "mychannel", **data_manager})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.data_samples = assets.get_data_samples()
        for data_sample in self.data_samples:
            serializer = DataSampleRepSerializer(data={"channel": "mychannel", **data_sample})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.compute_plans = assets.get_compute_plans()
        for compute_plan in self.compute_plans:
            serializer = ComputePlanRepSerializer(data={"channel": "mychannel", **compute_plan})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.compute_tasks = assets.get_train_tasks() + assets.get_test_tasks() + assets.get_composite_tasks()
        for compute_task in self.compute_tasks:
            # Missing field from test data
            compute_task["logs_permission"] = {
                "public": True,
                "authorized_ids": [compute_task["owner"]],
            }
            if compute_task["error_type"] is None:
                del compute_task["error_type"]
            else:
                compute_task["error_type"] = failure_report_pb2.ErrorType.Name(
                    getattr(ComputeTaskErrorType, compute_task["error_type"]).value
                )
            serializer = ComputeTaskRepSerializer(data={"channel": "mychannel", **compute_task})
            serializer.is_valid(raise_exception=True)
            serializer.save()

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

    def test_computeplan_list_success(self):
        for compute_plan in self.compute_plans:
            if compute_plan["status"] == "PLAN_STATUS_UNKNOWN":
                del compute_plan["estimated_end_date"]
        response = self.client.get(self.url, **self.extra)
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

    @parameterized.expand(
        [
            ("PLAN_STATUS_WAITING",),
            ("PLAN_STATUS_TODO",),
            ("PLAN_STATUS_DOING",),
            ("PLAN_STATUS_DONE",),
            ("PLAN_STATUS_CANCELED",),
            ("PLAN_STATUS_FAILED",),
        ]
    )
    def test_computeplan_list_filter_by_status(self, status):
        """Filter computeplan on status."""
        filtered_compute_plans = [cp for cp in self.compute_plans if cp["status"] == status]
        params = urlencode({"search": f"compute_plan:status:{status}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(filtered_compute_plans), "next": None, "previous": None, "results": filtered_compute_plans},
        )

    def test_computeplan_retrieve(self):
        url = reverse("substrapp:compute_plan-detail", args=[self.compute_plans[0]["key"]])
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

    @internal_server_error_on_exception()
    @mock.patch(
        "substrapp.views.computeplan.ComputePlanViewSet.update_ledger", side_effect=Exception("Unexpected error")
    )
    def test_computeplan_update_ledger_fail_internal_server_error(self, _):
        url = reverse("substrapp:compute_plan-update-ledger", kwargs={"pk": self.compute_plans[0]["key"]})
        response = self.client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

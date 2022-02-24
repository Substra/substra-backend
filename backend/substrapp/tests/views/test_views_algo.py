import json
import logging
import os
import shutil
import tempfile
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.failure_report_pb2 as failure_report_pb2
from localrep.models import Algo as AlgoRep
from localrep.serializers import AlgoSerializer as AlgoRepSerializer
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from localrep.serializers import DataManagerSerializer as DataManagerRepSerializer
from localrep.serializers import DataSampleSerializer as DataSampleRepSerializer
from localrep.serializers import MetricSerializer as MetricRepSerializer
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from orchestrator.error import StatusCode
from substrapp.compute_tasks.errors import ComputeTaskErrorType

from .. import assets
from ..common import AuthenticatedClient
from ..common import internal_server_error_on_exception

MEDIA_ROOT = tempfile.mkdtemp()

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURE_PATH = os.path.join(DIR_PATH, "../../../../fixtures/chunantes/algos/algo3")


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class AlgoViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)
        self.url = reverse("substrapp:algo-list")

        self.algos = assets.get_algos()
        for algo in self.algos:
            serializer = AlgoRepSerializer(data={"channel": "mychannel", **algo})
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    def test_algo_list_empty(self):
        AlgoRep.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_algo_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(), {"count": len(self.algos), "next": None, "previous": None, "results": self.algos}
        )

    def test_algo_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.algo.AlgoViewSet.list", side_effect=Exception("Unexpected error"))
    def test_algo_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_algo_list_storage_addresses_update(self):
        for algo in AlgoRep.objects.all():
            algo.description_address.replace("http://testserver", "http://remotetestserver")
            algo.algorithm_address.replace("http://testserver", "http://remotetestserver")
            algo.save()

        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.data["count"], len(self.algos))
        for result, algo in zip(response.data["results"], self.algos):
            for field in ("description", "algorithm"):
                self.assertEqual(result[field]["storage_address"], algo[field]["storage_address"])

    def test_algo_list_filter(self):
        """Filter algo on key."""
        key = self.algos[0]["key"]
        params = urlencode({"search": f"algo:key:{key}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 1, "next": None, "previous": None, "results": self.algos[:1]})

    def test_algo_list_filter_and(self):
        """Filter algo on key and owner."""
        key, owner = self.algos[0]["key"], self.algos[0]["owner"]
        params = urlencode({"search": f"algo:key:{key},algo:owner:{owner}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 1, "next": None, "previous": None, "results": self.algos[:1]})

    def test_algo_list_filter_or(self):
        """Filter algo on key_0 or key_1."""
        key_0 = self.algos[0]["key"]
        key_1 = self.algos[1]["key"]
        params = urlencode({"search": f"algo:key:{key_0}-OR-algo:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 2, "next": None, "previous": None, "results": self.algos[:2]})

    def test_algo_list_filter_or_and(self):
        """Filter algo on (key_0 and owner_0) or (key_1 and owner_1)."""
        key_0, owner_0 = self.algos[0]["key"], self.algos[0]["owner"]
        key_1, owner_1 = self.algos[1]["key"], self.algos[1]["owner"]
        params = urlencode(
            {"search": f"algo:key:{key_0},algo:owner:{owner_0}-OR-algo:key:{key_1},algo:owner:{owner_1}"}
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 2, "next": None, "previous": None, "results": self.algos[:2]})

    @parameterized.expand(
        [
            ("ALGO_UNKNOWN",),
            ("ALGO_SIMPLE",),
            ("ALGO_AGGREGATE",),
            ("ALGO_COMPOSITE",),
        ]
    )
    def test_algo_list_filter_by_category(self, category):
        """Filter algo on category."""
        filtered_algos = [task for task in self.algos if task["category"] == category]
        params = urlencode({"search": f"algo:category:{category}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(filtered_algos), "next": None, "previous": None, "results": filtered_algos},
        )

    @parameterized.expand(
        [
            ("page_size_5_page_1", 5, 1),
            ("page_size_1_page_2", 1, 2),
            ("page_size_2_page_3", 2, 3),
        ]
    )
    def test_algo_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        self.assertEqual(r["count"], len(self.algos))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.algos[offset : offset + page_size])

    def test_algo_cp_list_success(self):
        """List algos for a specific compute plan (CPAlgoViewSet)."""

        metrics = assets.get_metrics()
        for metric in metrics:
            serializer = MetricRepSerializer(data={"channel": "mychannel", **metric})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        data_managers = assets.get_data_managers()
        for data_manager in data_managers:
            serializer = DataManagerRepSerializer(data={"channel": "mychannel", **data_manager})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        data_samples = assets.get_data_samples()
        for data_sample in data_samples:
            serializer = DataSampleRepSerializer(data={"channel": "mychannel", **data_sample})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        compute_plans = assets.get_compute_plans()
        for compute_plan in compute_plans:
            serializer = ComputePlanRepSerializer(data={"channel": "mychannel", **compute_plan})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        compute_tasks = assets.get_train_tasks() + assets.get_test_tasks() + assets.get_composite_tasks()
        for compute_task in compute_tasks:
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

        # Get a CP with more than one task to have "interesting" results
        compute_plan_key = [cp["key"] for cp in compute_plans if cp["task_count"] > 1][0]
        related_algo_keys = [ct["algo"]["key"] for ct in compute_tasks if ct["compute_plan_key"] == compute_plan_key]
        related_algos = [algo for algo in self.algos if algo["key"] in related_algo_keys]

        url = reverse("substrapp:compute_plan_algo-list", args=[compute_plan_key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(
            response.json(), {"count": len(related_algos), "next": None, "previous": None, "results": related_algos}
        )

    def test_algo_create(self):
        def mock_orc_response(data):
            """Build orchestrator register response from request data."""
            return {
                "key": data["key"],
                "name": data["name"],
                "owner": data["new_permissions"]["authorized_ids"][0],
                "permissions": {
                    "process": data["new_permissions"],
                    "download": data["new_permissions"],
                },
                "metadata": {},
                "category": algo_pb2.AlgoCategory.Name(data["category"]),
                "creation_date": "2021-11-04T13:54:09.882662Z",
                "description": data["description"],
                "algorithm": data["algorithm"],
            }

        algorithm_path = os.path.join(FIXTURE_PATH, "algo.tar.gz")
        description_path = os.path.join(FIXTURE_PATH, "description.md")
        data = {
            "json": json.dumps(
                {
                    "name": "Logistic regression",
                    "metric_key": "some key",
                    "category": "ALGO_SIMPLE",
                    "permissions": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                }
            ),
            "file": open(algorithm_path, "rb"),
            "description": open(description_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_algo", side_effect=mock_orc_response):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        self.assertIsNotNone(response.data["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # asset created in local db
        self.assertEqual(AlgoRep.objects.count(), len(self.algos) + 1)

        data["file"].close()
        data["description"].close()

    @override_settings(DATA_UPLOAD_MAX_SIZE=150)
    def test_file_size_limit(self):
        algorithm_path = os.path.join(FIXTURE_PATH, "algo.tar.gz")
        description_path = os.path.join(FIXTURE_PATH, "description.md")

        data = {
            "json": json.dumps(
                {
                    "name": "Logistic regression",
                    "metric_key": "some key",
                    "category": "ALGO_SIMPLE",
                    "permissions": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                }
            ),
            "file": open(algorithm_path, "rb"),
            "description": open(description_path, "rb"),
        }

        response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File too large", response.data["message"][0]["file"])

        data["description"].close()
        data["file"].close()

    def test_algo_create_fail_rollback(self):
        class MockOrcError(OrcError):
            code = StatusCode.ALREADY_EXISTS
            details = "already exists"

        algorithm_path = os.path.join(FIXTURE_PATH, "algo.tar.gz")
        description_path = os.path.join(FIXTURE_PATH, "description.md")
        data = {
            "json": json.dumps(
                {
                    "name": "Logistic regression",
                    "metric_key": "some key",
                    "category": "ALGO_SIMPLE",
                    "permissions": {
                        "public": True,
                        "authorized_ids": [],
                    },
                }
            ),
            "file": open(algorithm_path, "rb"),
            "description": open(description_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_algo", side_effect=MockOrcError()):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        # asset not created in local db
        self.assertEqual(AlgoRep.objects.count(), len(self.algos))
        # orc error code should be propagated
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.algo.AlgoViewSet.create", side_effect=Exception("Unexpected error"))
    def test_algo_create_fail(self, _):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @mock.patch("substrapp.views.algo.node_client.get", return_value=b"content")
    def test_algo_retrieve(self, _):
        url = reverse("substrapp:algo-detail", args=[self.algos[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.algos[0])

    def test_algo_retrieve_wrong_channel(self):
        url = reverse("substrapp:algo-detail", args=[self.algos[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @parameterized.expand([(True,), (False,)])
    @mock.patch("substrapp.views.algo.node_client.get", return_value=b"content")
    def test_algo_retrieve_storage_addresses_update(self, has_cache, _):
        algo = AlgoRep.objects.get(key=self.algos[0]["key"])
        algo.description_address.replace("http://testserver", "http://remotetestserver")
        algo.algorithm_address.replace("http://testserver", "http://remotetestserver")
        algo.save()

        url = reverse("substrapp:algo-detail", args=[self.algos[0]["key"]])
        with mock.patch("substrapp.views.algo.node_has_process_permission", return_value=has_cache):
            response = self.client.get(url, **self.extra)
        for field in ("description", "algorithm"):
            self.assertEqual(response.data[field]["storage_address"], self.algos[0][field]["storage_address"])

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.algo.AlgoViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_algo_retrieve_fail(self, _):
        url = reverse("substrapp:algo-detail", args=[self.algos[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

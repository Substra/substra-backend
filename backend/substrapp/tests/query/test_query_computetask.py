import os
import shutil
import tempfile
from unittest import mock
from uuid import uuid4

from django.test import override_settings
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from localrep.serializers import AlgoSerializer as AlgoRepSerializer
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from localrep.serializers import DataManagerSerializer as DataManagerRepSerializer
from localrep.serializers import DataSampleSerializer as DataSampleRepSerializer
from localrep.serializers import MetricSerializer as MetricRepSerializer
from orchestrator.client import OrchestratorClient

from .. import assets
from ..common import AuthenticatedClient

TEST_ORG = "MyTestOrg"
MEDIA_ROOT = tempfile.mkdtemp()


class ComputeTaskQueryTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

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

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def clean_input_data(self, compute_task):
        compute_task["logs_permission"] = {
            "public": True,
            "authorized_ids": [compute_task["owner"]],
        }
        del compute_task["error_type"]
        return compute_task


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class TrainTaskQueryTests(ComputeTaskQueryTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("substrapp:traintuple-list")

    @parameterized.expand([("with_compute_plan", True), ("without_compute_plan", False)])
    def test_add_traintask_ok(self, _, with_compute_plan):
        train_task = assets.get_train_task()
        train_task = self.clean_input_data(train_task)
        train_task["compute_plan_key"] = self.compute_plans[0]["key"]

        data = {
            "algo_key": train_task["algo"]["key"],
            "data_manager_key": train_task["train"]["data_manager_key"],
            "train_data_sample_keys": train_task["train"]["data_sample_keys"],
        }
        if with_compute_plan:
            data["compute_plan_key"] = train_task["compute_plan_key"]

        with mock.patch.object(OrchestratorClient, "register_tasks", return_value=[train_task]) as mregister_task:
            with mock.patch.object(
                OrchestratorClient, "register_compute_plan", return_value=self.compute_plans[0]
            ) as mregister_compute_plan:
                response = self.client.post(self.url, data, format="json", **self.extra)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(mregister_task.call_count, 1)
                if with_compute_plan:
                    self.assertEqual(mregister_compute_plan.call_count, 0)
                else:
                    self.assertEqual(mregister_compute_plan.call_count, 1)

    def test_add_traintask_ko(self):
        train_task = assets.get_train_task()
        train_task = self.clean_input_data(train_task)

        data = {
            "data_manager_key": train_task["train"]["data_manager_key"],
            "train_data_sample_keys": train_task["train"]["data_sample_keys"],
        }

        with mock.patch.object(OrchestratorClient, "register_compute_plan", return_value=self.compute_plans[0]):
            response = self.client.post(self.url, data, format="json", **self.extra)
            self.assertIn("This field may not be null.", response.json()["algo_key"])
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class TestTaskQueryTests(ComputeTaskQueryTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("substrapp:testtuple-list")

    @parameterized.expand([("with_data_manager", True), ("without_data_manager", False)])
    def test_add_testtask_ok(self, _, with_data_manager):
        train_task = assets.get_train_task()
        train_task = self.clean_input_data(train_task)
        serializer = ComputeTaskRepSerializer(data={"channel": "mychannel", **train_task})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        test_task = assets.get_test_task()
        test_task = self.clean_input_data(test_task)
        test_task["parent_task_keys"] = [train_task["key"]]

        data = {
            "algo_key": test_task["algo"]["key"],
            "metric_key": test_task["algo"]["key"],
            "test_data_sample_keys": test_task["test"]["data_sample_keys"],
            "traintuple_key": train_task["key"],
        }
        if with_data_manager:
            data["data_manager_key"] = test_task["test"]["data_manager_key"]

        with mock.patch.object(OrchestratorClient, "register_tasks", return_value=[test_task]):
            response = self.client.post(self.url, data, format="json", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_testtask_ko(self):
        test_task = assets.get_test_task()
        test_task = self.clean_input_data(test_task)

        data = {
            "algo_key": test_task["algo"]["key"],
            "metric_key": test_task["algo"]["key"],
            "test_data_sample_keys": test_task["test"]["data_sample_keys"],
        }

        response = self.client.post(self.url, data, format="json", **self.extra)
        self.assertIn("This field may not be null.", response.json()["message"][0]["traintuple_key"])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    LEDGER_MSP_ID=TEST_ORG,
)
class CompositeTaskQueryTests(ComputeTaskQueryTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("substrapp:composite_traintuple-list")

    @parameterized.expand([("with_in_models_and_cp", True, True), ("without_in_models", False, False)])
    def test_add_compositetask_ok(self, _, with_in_models, with_compute_plan):
        composite_task = assets.get_composite_task()
        composite_task = self.clean_input_data(composite_task)
        composite_task["compute_plan_key"] = self.compute_plans[0]["key"]

        data = {
            "algo_key": composite_task["algo"]["key"],
            "metric_key": composite_task["algo"]["key"],
            "data_manager_key": composite_task["composite"]["data_manager_key"],
            "train_data_sample_keys": composite_task["composite"]["data_sample_keys"],
            "out_trunk_model_permissions": {
                "public": False,
                "authorized_ids": ["Node-1", "Node-2"],
            },
        }
        if with_compute_plan:
            data["compute_plan_key"] = composite_task["compute_plan_key"]
        if with_in_models:
            data["in_head_model_key"] = uuid4()
            data["in_trunk_model_key"] = uuid4()

        with mock.patch.object(OrchestratorClient, "register_tasks", return_value=[composite_task]) as mregister_task:
            with mock.patch.object(
                OrchestratorClient, "register_compute_plan", return_value=self.compute_plans[0]
            ) as mregister_compute_plan:
                response = self.client.post(self.url, data, format="json", **self.extra)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(mregister_task.call_count, 1)
                if with_compute_plan:
                    self.assertEqual(mregister_compute_plan.call_count, 0)
                else:
                    self.assertEqual(mregister_compute_plan.call_count, 1)

    def test_add_compositetraintuple_ko(self):
        composite_task = assets.get_composite_task()
        composite_task = self.clean_input_data(composite_task)

        data = {
            "metric_key": composite_task["algo"]["key"],
            "data_manager_key": composite_task["composite"]["data_manager_key"],
            "train_data_sample_keys": composite_task["composite"]["data_sample_keys"],
        }

        with mock.patch.object(OrchestratorClient, "register_compute_plan", return_value=self.compute_plans[0]):
            response = self.client.post(self.url, data, format="multipart", **self.extra)
            print(response.json())
            self.assertIn("This field may not be null.", response.json()["algo_key"])
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

import os
import shutil
import tempfile

from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APITestCase

from localrep.models import Algo as AlgoRep
from localrep.models import ComputePlan as ComputePlanRep
from localrep.models import ComputeTask as ComputeTaskRep
from localrep.models import Performance as PerformanceRep
from substrapp.tests import factory

from ..common import AuthenticatedClient

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
)
class CPPerformanceViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.data_manager = factory.create_datamanager()
        self.data_sample = factory.create_datasample([self.data_manager])
        self.compute_plan = factory.create_computeplan()

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        self.url = reverse("substrapp:compute_plan_perf-list", args=[self.compute_plan.key])

        self.metric = factory.create_algo(category=AlgoRep.Category.ALGO_METRIC)
        self.compute_tasks = [
            factory.create_computetask(
                self.compute_plan,
                algo=self.metric,
                data_manager=self.data_manager,
                data_samples=[self.data_sample.key],
                category=ComputeTaskRep.Category.TASK_TEST,
                status=ComputeTaskRep.Status.STATUS_DONE,
                rank=i + 1,
                metadata={"round_idx": 1},
                error_type=None,
            )
            for i in range(3)
        ]
        self.performances = [factory.create_performance(self.compute_tasks[i], self.metric) for i in range(3)]
        self.expected_stats = {
            "compute_tasks_distinct_ranks": [1, 2, 3],
            "compute_tasks_distinct_rounds": [1],
        }
        self.expected_results = [
            {
                "compute_task": {
                    "key": str(self.compute_tasks[0].key),
                    "data_manager_key": str(self.data_manager.key),
                    "algo_key": str(self.metric.key),
                    "rank": 1,
                    "round_idx": 1,
                    "data_samples": [str(self.data_sample.key)],
                    "worker": "MyOrg1MSP",
                },
                "metric": {
                    "key": str(self.metric.key),
                    "name": self.metric.name,
                },
                "perf": self.performances[0].value,
            },
            {
                "compute_task": {
                    "key": str(self.compute_tasks[1].key),
                    "data_manager_key": str(self.data_manager.key),
                    "algo_key": str(self.metric.key),
                    "rank": 2,
                    "round_idx": 1,
                    "data_samples": [str(self.data_sample.key)],
                    "worker": "MyOrg1MSP",
                },
                "metric": {
                    "key": str(self.metric.key),
                    "name": self.metric.name,
                },
                "perf": self.performances[1].value,
            },
            {
                "compute_task": {
                    "key": str(self.compute_tasks[2].key),
                    "data_manager_key": str(self.data_manager.key),
                    "algo_key": str(self.metric.key),
                    "rank": 3,
                    "round_idx": 1,
                    "data_samples": [str(self.data_sample.key)],
                    "worker": "MyOrg1MSP",
                },
                "metric": {
                    "key": str(self.metric.key),
                    "name": self.metric.name,
                },
                "perf": self.performances[2].value,
            },
        ]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_performance_list_empty(self):
        PerformanceRep.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {
                "count": 0,
                "next": None,
                "previous": None,
                "compute_plan_statistics": {
                    "compute_tasks_distinct_ranks": [1, 2, 3],
                    "compute_tasks_distinct_rounds": [1],
                },
                "results": [],
            },
        )

    def test_performance_list(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {
                "count": len(self.expected_results),
                "next": None,
                "previous": None,
                "compute_plan_statistics": self.expected_stats,
                "results": self.expected_results,
            },
        )


class PerformanceViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.maxDiff = None
        self.data_manager = factory.create_datamanager()
        self.data_sample = factory.create_datasample([self.data_manager])
        self.compute_plans = [
            factory.create_computeplan(status=ComputePlanRep.Status.PLAN_STATUS_DOING),
            factory.create_computeplan(status=ComputePlanRep.Status.PLAN_STATUS_DONE),
        ]

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        self.url = reverse("substrapp:performance-list")
        self.export_extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "*/*"}
        self.export_url = reverse("substrapp:performance-export")

        self.metrics = [factory.create_algo(category=AlgoRep.Category.ALGO_METRIC) for _ in range(3)]
        self.compute_tasks = [
            factory.create_computetask(
                self.compute_plans[i],
                algo=self.metrics[i],
                data_manager=self.data_manager,
                data_samples=[self.data_sample.key],
                category=ComputeTaskRep.Category.TASK_TEST,
                status=ComputeTaskRep.Status.STATUS_DONE,
                error_type=None,
            )
            for i in range(2)
        ]
        self.performances = [factory.create_performance(self.compute_tasks[0], self.metrics[i]) for i in range(3)]
        self.performances.extend([factory.create_performance(self.compute_tasks[1], self.metrics[i]) for i in range(3)])
        self.expected_results = [
            {
                "compute_plan_key": self.compute_plans[0],
                "compute_plan_name": None,
                "compute_plan_tag": "",
                "compute_plan_status": "PLAN_STATUS_TODO",
                "compute_plan_start_date": None,
                "compute_plan_end_date": None,
                "compute_plan_metadata": {},
                "compute_task__metadata": {},
                "metric_name": "metric",
                "worker": "MyOrg1MSP",
                "test_task_rank": 1,
                "test_task_round": None,
                "performance": 1.0,
            },
            {
                "compute_plan_key": self.compute_plans[0],
                "compute_plan_name": None,
                "compute_plan_tag": "",
                "compute_plan_status": "PLAN_STATUS_TODO",
                "compute_plan_start_date": None,
                "compute_plan_end_date": None,
                "compute_plan_metadata": {},
                "compute_task__metadata": {},
                "metric_name": "metric",
                "worker": "MyOrg1MSP",
                "test_task_rank": 1,
                "test_task_round": None,
                "performance": 1.0,
            },
            {
                "compute_plan_key": self.compute_plans[0],
                "compute_plan_name": None,
                "compute_plan_tag": "",
                "compute_plan_status": "PLAN_STATUS_TODO",
                "compute_plan_start_date": None,
                "compute_plan_end_date": None,
                "compute_plan_metadata": {},
                "compute_task__metadata": {},
                "metric_name": "metric",
                "worker": "MyOrg1MSP",
                "test_task_rank": 1,
                "test_task_round": None,
                "performance": 1.0,
            },
            {
                "compute_plan_key": self.compute_plans[1],
                "compute_plan_name": None,
                "compute_plan_tag": "",
                "compute_plan_status": "PLAN_STATUS_TODO",
                "compute_plan_start_date": None,
                "compute_plan_end_date": None,
                "compute_plan_metadata": {},
                "compute_task__metadata": {},
                "metric_name": "metric",
                "worker": "MyOrg1MSP",
                "test_task_rank": 1,
                "test_task_round": None,
                "performance": 1.0,
            },
            {
                "compute_plan_key": self.compute_plans[1],
                "compute_plan_name": None,
                "compute_plan_tag": "",
                "compute_plan_status": "PLAN_STATUS_TODO",
                "compute_plan_start_date": None,
                "compute_plan_end_date": None,
                "compute_plan_metadata": {},
                "compute_task__metadata": {},
                "metric_name": "metric",
                "worker": "MyOrg1MSP",
                "test_task_rank": 1,
                "test_task_round": None,
                "performance": 1.0,
            },
            {
                "compute_plan_key": self.compute_plans[1],
                "compute_plan_name": None,
                "compute_plan_tag": "",
                "compute_plan_status": "PLAN_STATUS_TODO",
                "compute_plan_start_date": None,
                "compute_plan_end_date": None,
                "compute_plan_metadata": {},
                "compute_task__metadata": {},
                "metric_name": "metric",
                "worker": "MyOrg1MSP",
                "test_task_rank": 1,
                "test_task_round": None,
                "performance": 1.0,
            },
        ]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_performance_view(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_performance_export(self):
        response = self.client.get(self.export_url, **self.export_extra)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list(response.streaming_content)), len(self.expected_results) + 1)

    def test_performance_export_with_metadata(self):
        metadata = "epochs,hidden_sizes,last_hidden_sizes"
        params = urlencode({"metadata": metadata})
        response = self.client.get(f"{self.export_url}?{params}", **self.export_extra)
        content_list = list(response.streaming_content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(metadata in str(content_list[0]))
        self.assertEqual(len(content_list), len(self.expected_results) + 1)

    def test_performance_export_filter(self):
        """Filter performance on cp key."""
        key = self.compute_plans[0].key
        params = urlencode({"key": key})
        response = self.client.get(f"{self.export_url}?{params}", **self.export_extra)
        content_list = list(response.streaming_content)
        self.assertEqual(len(content_list), 4)
        self.assertTrue(str(self.compute_plans[0].key) in str(content_list[1]))

    def test_performance_export_filter_in(self):
        """Filter performance on cp in key_0, key_1."""
        key_0 = self.compute_plans[0].key
        key_1 = self.compute_plans[1].key
        params = urlencode({"key": ",".join([str(key_0), str(key_1)])})
        response = self.client.get(f"{self.export_url}?{params}", **self.export_extra)
        content_list = list(response.streaming_content)
        self.assertEqual(len(content_list), len(self.expected_results) + 1)

    def test_performance_export_filter_and(self):
        """Filter performance on cp key and status."""
        key_0 = self.compute_plans[0].key
        key_1 = self.compute_plans[1].key
        status = ComputePlanRep.Status.PLAN_STATUS_DOING
        params = urlencode({"key": ",".join([str(key_0), str(key_1)]), "status": status})
        response = self.client.get(f"{self.export_url}?{params}", **self.export_extra)
        content_list = list(response.streaming_content)
        self.assertEqual(len(content_list), 4)
        self.assertTrue(status in str(content_list[1]))

import os
import shutil
import tempfile

import pytest
from django.db import connection
from django.test import override_settings
from django.test import utils
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import ComputePlan
from api.models import ComputeTask
from api.models import Performance
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient
from substrapp.tests.common import InputIdentifiers

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
        self.url = reverse("api:compute_plan_perf-list", args=[self.compute_plan.key])

        self.metric = factory.create_function(
            outputs=factory.build_function_outputs(["performance"]),
        )

        input_keys = {
            "opener": [self.data_manager.key],
            "datasamples": [self.data_sample.key],
        }
        self.inputs = factory.build_computetask_inputs(self.metric, input_keys)
        self.compute_tasks = [
            factory.create_computetask(
                self.compute_plan,
                self.metric,
                inputs=self.inputs,
                outputs=factory.build_computetask_outputs(self.metric),
                status=ComputeTask.Status.STATUS_DONE,
                rank=i + 1,
                metadata={"round_idx": 1},
                error_type=None,
            )
            for i in range(3)
        ]
        self.performances = []
        for i in range(3):
            self.performances += [
                factory.create_performance(
                    output,
                    self.metric,
                )
                for output in self.compute_tasks[i].outputs.all()
            ]
        self.expected_stats = {
            "compute_tasks_distinct_ranks": [1, 2, 3],
            "compute_tasks_distinct_rounds": [1],
        }
        self.expected_results = [
            {
                "compute_task": {
                    "key": str(self.compute_tasks[0].key),
                    "function_key": str(self.metric.key),
                    "rank": 1,
                    "round_idx": 1,
                    "worker": "MyOrg1MSP",
                },
                "identifier": InputIdentifiers.PERFORMANCE,
                "metric": {
                    "key": str(self.metric.key),
                    "name": self.metric.name,
                },
                "perf": self.performances[0].value,
            },
            {
                "compute_task": {
                    "key": str(self.compute_tasks[1].key),
                    "function_key": str(self.metric.key),
                    "rank": 2,
                    "round_idx": 1,
                    "worker": "MyOrg1MSP",
                },
                "identifier": InputIdentifiers.PERFORMANCE,
                "metric": {
                    "key": str(self.metric.key),
                    "name": self.metric.name,
                },
                "perf": self.performances[1].value,
            },
            {
                "compute_task": {
                    "key": str(self.compute_tasks[2].key),
                    "function_key": str(self.metric.key),
                    "rank": 3,
                    "round_idx": 1,
                    "worker": "MyOrg1MSP",
                },
                "identifier": InputIdentifiers.PERFORMANCE,
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
        Performance.objects.all().delete()
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

        self.data_manager = factory.create_datamanager()
        self.data_sample = factory.create_datasample([self.data_manager])
        self.compute_plans = [
            factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DOING),
            factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DONE),
        ]

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        self.url = reverse("api:performance-list")
        self.export_extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "*/*"}
        self.export_url = reverse("api:performance-export")

        self.metrics = [
            factory.create_function(
                outputs=factory.build_function_outputs(["performance"]),
            )
            for _ in range(3)
        ]
        self.compute_tasks = [
            factory.create_computetask(
                self.compute_plans[i],
                self.metrics[i],
                outputs=factory.build_computetask_outputs(self.metrics[i]),
                status=ComputeTask.Status.STATUS_DONE,
                error_type=None,
            )
            for i in range(2)
        ]
        self.performances = []
        for i in range(3):
            self.performances += [
                factory.create_performance(
                    output,
                    self.metrics[i],
                )
                for output in self.compute_tasks[0].outputs.all()
            ]

            self.performances += [
                factory.create_performance(
                    output,
                    self.metrics[i],
                )
                for output in self.compute_tasks[1].outputs.all()
            ]

        self.expected_results = [
            {
                "compute_plan_key": self.compute_plans[0],
                "compute_plan_name": None,
                "compute_plan_tag": "",
                "compute_plan_status": "PLAN_STATUS_TODO",
                "compute_plan_start_date": None,
                "compute_plan_end_date": None,
                "compute_plan_metadata": {},
                "compute_task_output__task__metadata": {},
                "function_name": "metric",
                "worker": "MyOrg1MSP",
                "task_rank": 1,
                "task_round": None,
                "identifier": "performance",
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
                "compute_task_output__task__metadata": {},
                "function_name": "metric",
                "worker": "MyOrg1MSP",
                "task_rank": 1,
                "task_round": None,
                "identifier": "performance",
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
                "compute_task_output__task__metadata": {},
                "function_name": "metric",
                "worker": "MyOrg1MSP",
                "task_rank": 1,
                "task_round": None,
                "identifier": "performance",
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
                "compute_task_output__task__metadata": {},
                "function_name": "metric",
                "worker": "MyOrg1MSP",
                "task_rank": 1,
                "task_round": None,
                "identifier": "performance",
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
                "compute_task_output__task__metadata": {},
                "function_name": "metric",
                "worker": "MyOrg1MSP",
                "task_rank": 1,
                "task_round": None,
                "identifier": "performance",
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
                "compute_task_output__task__metadata": {},
                "function_name": "metric",
                "worker": "MyOrg1MSP",
                "task_rank": 1,
                "task_round": None,
                "identifier": "performance",
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
        params = urlencode({"metadata_columns": metadata})
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
        status = ComputePlan.Status.PLAN_STATUS_DOING
        params = urlencode({"key": ",".join([str(key_0), str(key_1)]), "status": status})
        response = self.client.get(f"{self.export_url}?{params}", **self.export_extra)
        content_list = list(response.streaming_content)
        self.assertEqual(len(content_list), 4)
        self.assertTrue(status in str(content_list[1]))


@pytest.mark.django_db
def test_n_plus_one_queries_performance_list(authenticated_client, create_compute_plan):
    # Dummy request, the fist request seems to trigger a caching system caching 4 requests
    url = reverse("api:compute_plan-list")
    authenticated_client.get(url)

    compute_plan = create_compute_plan(n_task=4)
    url = reverse("api:compute_plan_perf-list", args=[compute_plan.key])
    with utils.CaptureQueriesContext(connection) as query:
        authenticated_client.get(url)
    query_tasks_empty = len(query.captured_queries)

    for t in compute_plan.compute_tasks.all():
        perf_output = t.outputs.all()[1]
        factory.create_performance(perf_output, t.function)
    with utils.CaptureQueriesContext(connection) as query:
        print(authenticated_client.get(url))
    query_task_with_perf = len(query.captured_queries)
    assert query_task_with_perf < 12
    assert query_task_with_perf - query_tasks_empty < 4

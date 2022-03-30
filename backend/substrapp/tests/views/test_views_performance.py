import os
import shutil
import tempfile

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

import orchestrator.computetask_pb2 as computetask_pb2
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

        self.algo = factory.create_algo()
        self.data_manager = factory.create_datamanager()
        self.data_sample = factory.create_datasample([self.data_manager])
        self.compute_plan = factory.create_computeplan()

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        self.url = reverse("substrapp:compute_plan_perf-list", args=[self.compute_plan.key])

        self.metrics = [factory.create_metric() for _ in range(3)]
        self.compute_task = factory.create_computetask(
            self.compute_plan,
            algo=self.algo,
            metrics=self.metrics,
            data_manager=self.data_manager,
            data_samples=[self.data_sample.key],
            category=computetask_pb2.TASK_TEST,
            status=computetask_pb2.STATUS_DONE,
            error_type=None,
        )
        self.performances = [factory.create_performance(self.compute_task, self.metrics[i]) for i in range(3)]
        self.expected_results = [
            {
                "compute_task": {
                    "key": str(self.compute_task.key),
                    "data_manager_key": str(self.data_manager.key),
                    "algo_key": str(self.algo.key),
                    "rank": 1,
                    "epoch": None,
                    "round_idx": None,
                    "data_samples": [str(self.data_sample.key)],
                    "worker": "MyOrg1MSP",
                },
                "metric": {
                    "key": str(self.metrics[0].key),
                    "name": self.metrics[0].name,
                },
                "perf": self.performances[0].value,
            },
            {
                "compute_task": {
                    "key": str(self.compute_task.key),
                    "data_manager_key": str(self.data_manager.key),
                    "algo_key": str(self.algo.key),
                    "rank": 1,
                    "epoch": None,
                    "round_idx": None,
                    "data_samples": [str(self.data_sample.key)],
                    "worker": "MyOrg1MSP",
                },
                "metric": {
                    "key": str(self.metrics[1].key),
                    "name": self.metrics[1].name,
                },
                "perf": self.performances[1].value,
            },
            {
                "compute_task": {
                    "key": str(self.compute_task.key),
                    "data_manager_key": str(self.data_manager.key),
                    "algo_key": str(self.algo.key),
                    "rank": 1,
                    "epoch": None,
                    "round_idx": None,
                    "data_samples": [str(self.data_sample.key)],
                    "worker": "MyOrg1MSP",
                },
                "metric": {
                    "key": str(self.metrics[2].key),
                    "name": self.metrics[2].name,
                },
                "perf": self.performances[2].value,
            },
        ]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_performance_list_empty(self):
        PerformanceRep.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_performance_list(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

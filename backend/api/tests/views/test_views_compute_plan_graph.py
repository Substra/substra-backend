import os
import shutil
import tempfile

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import ComputeTask
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient
from api.views.compute_plan_graph import MAX_TASKS_DISPLAYED

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
)
class ComputePlanGraphViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        self.base_url = "api:workflow_graph"

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_empty_graph(self):
        compute_plan = factory.create_computeplan()
        url = reverse(self.base_url, args=[compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), {"tasks": [], "edges": []})

    def test_too_many_tasks(self):
        compute_plan = factory.create_computeplan()
        algo = factory.create_algo()
        for _ in range(MAX_TASKS_DISPLAYED + 1):
            factory.create_computetask(
                compute_plan,
                algo=algo,
            )
        url = reverse(self.base_url, args=[compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cp_graph(self):
        compute_plan = factory.create_computeplan()
        algo = factory.create_algo()
        train_task = factory.create_computetask(
            compute_plan,
            algo=algo,
            category=ComputeTask.Category.TASK_TRAIN,
        )
        predict_task = factory.create_computetask(
            compute_plan, algo=algo, category=ComputeTask.Category.TASK_PREDICT, parent_tasks=[train_task.key]
        )
        test_task = factory.create_computetask(
            compute_plan, algo=algo, category=ComputeTask.Category.TASK_TEST, parent_tasks=[predict_task.key]
        )
        composite_task = factory.create_computetask(
            compute_plan,
            algo=algo,
            category=ComputeTask.Category.TASK_COMPOSITE,
        )
        aggregate_task = factory.create_computetask(
            compute_plan, algo=algo, category=ComputeTask.Category.TASK_AGGREGATE, parent_tasks=[composite_task.key]
        )

        expected_results = {
            "tasks": [
                {
                    "key": str(train_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
                    "status": "STATUS_TODO",
                    "category": "TASK_TRAIN",
                    "inputs": [{"id": "in/model", "kind": "model"}],
                    "outputs": [{"id": "out/model", "kind": "model"}],
                },
                {
                    "key": str(predict_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
                    "status": "STATUS_TODO",
                    "category": "TASK_PREDICT",
                    "inputs": [{"id": "in/tested_model", "kind": "model"}],
                    "outputs": [{"id": "out/predictions", "kind": "model"}],
                },
                {
                    "key": str(test_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
                    "status": "STATUS_TODO",
                    "category": "TASK_TEST",
                    "inputs": [{"id": "in/predictions", "kind": "model"}],
                    "outputs": [{"id": "out/perf", "kind": "performance"}],
                },
                {
                    "key": str(composite_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
                    "status": "STATUS_TODO",
                    "category": "TASK_COMPOSITE",
                    "inputs": [{"id": "in/head_model", "kind": "model"}, {"id": "in/trunk_model", "kind": "model"}],
                    "outputs": [{"id": "out/head_model", "kind": "model"}, {"id": "out/trunk_model", "kind": "model"}],
                },
                {
                    "key": str(aggregate_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
                    "status": "STATUS_TODO",
                    "category": "TASK_AGGREGATE",
                    "inputs": [{"id": "in/models[]", "kind": "model"}],
                    "outputs": [{"id": "out/model", "kind": "model"}],
                },
            ],
            "edges": [
                {
                    "source_task_key": str(train_task.key),
                    "source_task_category": "TASK_TRAIN",
                    "target_task_key": str(predict_task.key),
                    "target_task_category": "TASK_PREDICT",
                    "source_output_name": "out/model",
                    "target_input_name": "in/tested_model",
                },
                {
                    "source_task_key": str(predict_task.key),
                    "source_task_category": "TASK_PREDICT",
                    "target_task_key": str(test_task.key),
                    "target_task_category": "TASK_TEST",
                    "source_output_name": "out/predictions",
                    "target_input_name": "in/predictions",
                },
                {
                    "source_task_key": str(composite_task.key),
                    "source_task_category": "TASK_COMPOSITE",
                    "target_task_key": str(aggregate_task.key),
                    "target_task_category": "TASK_AGGREGATE",
                    "source_output_name": "out/trunk_model",
                    "target_input_name": "in/models[]",
                },
            ],
        }
        url = reverse(self.base_url, args=[compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), expected_results)

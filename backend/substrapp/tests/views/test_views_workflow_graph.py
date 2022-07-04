import os
import shutil
import tempfile

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from localrep.models import ComputeTask as ComputeTaskRep
from substrapp.tests import factory

from ..common import AuthenticatedClient

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
)
class WorkflowGraphViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_empty_workflow(self):
        compute_plan = factory.create_computeplan()
        url = reverse("substrapp:compute_plan_workflow_graph-list", args=[compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), {"tasks": [], "edges": []})

    def test_too_many_tasks(self):
        compute_plan = factory.create_computeplan()
        algo = factory.create_algo()
        for _ in range(301):
            factory.create_computetask(
                compute_plan,
                algo=algo,
            )
        url = reverse("substrapp:compute_plan_workflow_graph-list", args=[compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_workflow_graph(self):
        compute_plan = factory.create_computeplan()
        algo = factory.create_algo()
        train_task = factory.create_computetask(
            compute_plan,
            algo=algo,
            category=ComputeTaskRep.Category.TASK_TRAIN,
        )
        test_task = factory.create_computetask(
            compute_plan, algo=algo, category=ComputeTaskRep.Category.TASK_TEST, parent_tasks=[train_task.key]
        )
        composite_task = factory.create_computetask(
            compute_plan,
            algo=algo,
            category=ComputeTaskRep.Category.TASK_COMPOSITE,
        )
        aggregate_task = factory.create_computetask(
            compute_plan, algo=algo, category=ComputeTaskRep.Category.TASK_AGGREGATE, parent_tasks=[composite_task.key]
        )

        expected_results = {
            "tasks": [
                {
                    "key": str(train_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
                    "status": "STATUS_TODO",
                    "category": "TASK_TRAIN",
                    "source_task_keys": [],
                    "inputs": ["in/model"],
                    "outputs": ["out/model"],
                },
                {
                    "key": str(test_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
                    "status": "STATUS_TODO",
                    "category": "TASK_TEST",
                    "source_task_keys": [str(train_task.key)],
                    "inputs": ["in/tested_model"],
                    "outputs": [],
                },
                {
                    "key": str(composite_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
                    "status": "STATUS_TODO",
                    "category": "TASK_COMPOSITE",
                    "source_task_keys": [],
                    "inputs": ["in/head_model", "in/trunk_model"],
                    "outputs": ["out/head_model", "out/trunk_model"],
                },
                {
                    "key": str(aggregate_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
                    "status": "STATUS_TODO",
                    "category": "TASK_AGGREGATE",
                    "source_task_keys": [str(composite_task.key)],
                    "inputs": ["in/models[]"],
                    "outputs": ["out/model"],
                },
            ],
            "edges": [
                {
                    "source_task_key": str(train_task.key),
                    "target_task_key": str(test_task.key),
                    "source_output_name": "out/model",
                    "target_input_name": "in/tested_model",
                },
                {
                    "source_task_key": str(composite_task.key),
                    "target_task_key": str(aggregate_task.key),
                    "source_output_name": "out/trunk_model",
                    "target_input_name": "in/models[]",
                },
            ],
        }
        url = reverse("substrapp:compute_plan_workflow_graph-list", args=[compute_plan.key])
        response = self.client.get(url, **self.extra)
        print(response.json())
        self.assertEqual(response.json(), expected_results)

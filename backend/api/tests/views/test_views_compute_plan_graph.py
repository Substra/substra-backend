import os
import shutil
import tempfile

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
        function = factory.create_function()
        for _ in range(MAX_TASKS_DISPLAYED + 1):
            factory.create_computetask(
                compute_plan,
                function=function,
            )
        url = reverse(self.base_url, args=[compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cp_graph(self):
        compute_plan = factory.create_computeplan()

        function_train = factory.create_function(
            inputs=factory.build_function_inputs(["datasamples", "opener"]),
            outputs=factory.build_function_outputs(["model"]),
        )

        function_predict = factory.create_function(
            inputs=factory.build_function_inputs(["model"]),
            outputs=factory.build_function_outputs(["predictions"]),
        )

        function_test = factory.create_function(
            inputs=factory.build_function_inputs(["predictions"]),
            outputs=factory.build_function_outputs(["performance"]),
        )

        function_aggregate = factory.create_function(
            inputs=factory.build_function_inputs(["model"]),
            outputs=factory.build_function_outputs(["model"]),
        )

        train_task = factory.create_computetask(
            compute_plan,
            rank=1,
            function=function_train,
            outputs=factory.build_computetask_outputs(function_train),
        )

        predict_task = factory.create_computetask(
            compute_plan,
            rank=2,
            function=function_predict,
            inputs=factory.build_computetask_inputs(
                function_predict,
                {
                    "model": [train_task.key],
                },
            ),
            outputs=factory.build_computetask_outputs(function_predict),
        )

        test_task = factory.create_computetask(
            compute_plan,
            rank=3,
            function=function_test,
            inputs=factory.build_computetask_inputs(
                function_test,
                {
                    "predictions": [predict_task.key],
                },
            ),
            outputs=factory.build_computetask_outputs(function_test),
        )

        composite_task = factory.create_computetask(
            compute_plan,
            rank=10,
            function=function_train,
            outputs=factory.build_computetask_outputs(function_train),
        )

        aggregate_task = factory.create_computetask(
            compute_plan,
            rank=11,
            function=function_aggregate,
            inputs=factory.build_computetask_inputs(
                function_aggregate,
                {
                    "model": [composite_task.key, train_task.key],
                },
            ),
            outputs=factory.build_computetask_outputs(function_aggregate),
        )

        expected_results = {
            "tasks": [
                {
                    "key": str(train_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
                    "function_name": "function",
                    "status": "STATUS_TODO",
                    "inputs_specs": [
                        {"kind": "ASSET_DATA_SAMPLE", "identifier": "datasamples"},
                        {"kind": "ASSET_DATA_MANAGER", "identifier": "opener"},
                    ],
                    "outputs_specs": [{"kind": "ASSET_MODEL", "identifier": "model"}],
                },
                {
                    "key": str(predict_task.key),
                    "rank": 2,
                    "worker": "MyOrg1MSP",
                    "function_name": "function",
                    "status": "STATUS_TODO",
                    "inputs_specs": [
                        {"kind": "ASSET_MODEL", "identifier": "model"},
                    ],
                    "outputs_specs": [{"kind": "ASSET_MODEL", "identifier": "predictions"}],
                },
                {
                    "key": str(test_task.key),
                    "rank": 3,
                    "worker": "MyOrg1MSP",
                    "function_name": "function",
                    "status": "STATUS_TODO",
                    "inputs_specs": [
                        {"kind": "ASSET_MODEL", "identifier": "predictions"},
                    ],
                    "outputs_specs": [{"kind": "ASSET_PERFORMANCE", "identifier": "performance"}],
                },
                {
                    "key": str(composite_task.key),
                    "rank": 10,
                    "worker": "MyOrg1MSP",
                    "function_name": "function",
                    "status": "STATUS_TODO",
                    "inputs_specs": [
                        {"kind": "ASSET_DATA_SAMPLE", "identifier": "datasamples"},
                        {"kind": "ASSET_DATA_MANAGER", "identifier": "opener"},
                    ],
                    "outputs_specs": [{"kind": "ASSET_MODEL", "identifier": "model"}],
                },
                {
                    "key": str(aggregate_task.key),
                    "rank": 11,
                    "worker": "MyOrg1MSP",
                    "function_name": "function",
                    "status": "STATUS_TODO",
                    "inputs_specs": [
                        {"kind": "ASSET_MODEL", "identifier": "model"},
                    ],
                    "outputs_specs": [{"kind": "ASSET_MODEL", "identifier": "model"}],
                },
            ],
            "edges": [
                {
                    "source_task_key": str(train_task.key),
                    "target_task_key": str(predict_task.key),
                    "source_output_identifier": "model",
                    "target_input_identifier": "model",
                },
                {
                    "source_task_key": str(predict_task.key),
                    "target_task_key": str(test_task.key),
                    "source_output_identifier": "predictions",
                    "target_input_identifier": "predictions",
                },
                {
                    "source_task_key": str(composite_task.key),
                    "target_task_key": str(aggregate_task.key),
                    "source_output_identifier": "model",
                    "target_input_identifier": "model",
                },
                {
                    "source_task_key": str(train_task.key),
                    "target_task_key": str(aggregate_task.key),
                    "source_output_identifier": "model",
                    "target_input_identifier": "model",
                },
            ],
        }
        url = reverse(self.base_url, args=[compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), expected_results)

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

        algo_train = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener"]),
            outputs=factory.build_algo_outputs(["model"]),
        )

        algo_predict = factory.create_algo(
            inputs=factory.build_algo_inputs(["model"]),
            outputs=factory.build_algo_outputs(["predictions"]),
        )

        algo_test = factory.create_algo(
            inputs=factory.build_algo_inputs(["predictions"]),
            outputs=factory.build_algo_outputs(["performance"]),
        )

        algo_aggregate = factory.create_algo(
            inputs=factory.build_algo_inputs(["model"]),
            outputs=factory.build_algo_outputs(["model"]),
        )

        train_task = factory.create_computetask(
            compute_plan,
            rank=1,
            algo=algo_train,
            outputs=factory.build_computetask_outputs(algo_train),
        )

        predict_task = factory.create_computetask(
            compute_plan,
            rank=2,
            algo=algo_predict,
            inputs=factory.build_computetask_inputs(
                algo_predict,
                {
                    "model": [train_task.key],
                },
            ),
            outputs=factory.build_computetask_outputs(algo_predict),
        )

        test_task = factory.create_computetask(
            compute_plan,
            rank=3,
            algo=algo_test,
            inputs=factory.build_computetask_inputs(
                algo_test,
                {
                    "predictions": [predict_task.key],
                },
            ),
            outputs=factory.build_computetask_outputs(algo_test),
        )

        composite_task = factory.create_computetask(
            compute_plan,
            rank=10,
            algo=algo_train,
            outputs=factory.build_computetask_outputs(algo_train),
        )

        aggregate_task = factory.create_computetask(
            compute_plan,
            rank=11,
            algo=algo_aggregate,
            inputs=factory.build_computetask_inputs(
                algo_aggregate,
                {
                    "model": [composite_task.key, train_task.key],
                },
            ),
            outputs=factory.build_computetask_outputs(algo_aggregate),
        )

        expected_results = {
            "tasks": [
                {
                    "key": str(train_task.key),
                    "rank": 1,
                    "worker": "MyOrg1MSP",
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

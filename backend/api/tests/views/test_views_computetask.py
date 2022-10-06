import logging
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

from api.models import ComputeTask
from api.models import Model
from api.models import Performance
from api.serializers import AlgoSerializer
from api.serializers import DataManagerSerializer
from api.serializers import DataSampleSerializer
from api.serializers import ModelSerializer
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient
from api.tests.common import internal_server_error_on_exception
from api.views.computetask import EXTRA_DATA_FIELD
from orchestrator.client import OrchestratorClient
from orchestrator.resources import TAG_KEY

MEDIA_ROOT = tempfile.mkdtemp()


class ComputeTaskViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

        self.simple_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "model"]),
            outputs=factory.build_algo_outputs(["model"]),
            name="simple algo",
        )
        self.aggregate_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["models"]),
            outputs=factory.build_algo_outputs(["model"]),
            name="aggregate",
        )
        self.composite_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "local", "shared"]),
            outputs=factory.build_algo_outputs(["local", "shared"]),
            name="composite",
        )
        self.predict_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "model", "shared"]),
            outputs=factory.build_algo_outputs(["predictions"]),
            name="predict",
        )
        self.metric_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "predictions"]),
            outputs=factory.build_algo_outputs(["performance"]),
            name="metric",
        )
        self.data_manager = factory.create_datamanager()
        self.data_sample = factory.create_datasample([self.data_manager])
        self.compute_plan = factory.create_computeplan()

        self.compute_tasks = {}
        input_keys = {
            "opener": [self.data_manager.key],
            "datasamples": [self.data_sample.key],
        }
        for algo, category in (
            (self.simple_algo, ComputeTask.Category.TASK_TRAIN),
            (self.metric_algo, ComputeTask.Category.TASK_TEST),
            (self.composite_algo, ComputeTask.Category.TASK_COMPOSITE),
        ):
            self.compute_tasks[category] = {}
            for _status in (
                ComputeTask.Status.STATUS_TODO,
                ComputeTask.Status.STATUS_WAITING,
                ComputeTask.Status.STATUS_DOING,
                ComputeTask.Status.STATUS_DONE,
                ComputeTask.Status.STATUS_FAILED,
                ComputeTask.Status.STATUS_CANCELED,
            ):
                error_type = (
                    ComputeTask.ErrorType.ERROR_TYPE_EXECUTION if _status == ComputeTask.Status.STATUS_FAILED else None
                )
                self.compute_tasks[category][_status] = factory.create_computetask(
                    self.compute_plan,
                    algo,
                    inputs=factory.build_computetask_inputs(algo, input_keys),
                    outputs=factory.build_computetask_outputs(algo),
                    data_manager=self.data_manager,
                    data_samples=[self.data_sample.key],
                    category=category,
                    status=_status,
                    error_type=error_type,
                )

        self.done_train_task = self.compute_tasks[ComputeTask.Category.TASK_TRAIN][ComputeTask.Status.STATUS_DONE]
        self.train_model = factory.create_model(self.done_train_task, identifier="model")

        done_composite_task = self.compute_tasks[ComputeTask.Category.TASK_COMPOSITE][ComputeTask.Status.STATUS_DONE]
        self.local_model = factory.create_model(done_composite_task, identifier="local")
        self.shared_model = factory.create_model(done_composite_task, identifier="shared")

        done_test_task = self.compute_tasks[ComputeTask.Category.TASK_TEST][ComputeTask.Status.STATUS_DONE]
        self.performance = factory.create_performance(done_test_task, self.metric_algo)

        # we don't explicitly serialize relationships as this test module is focused on computetask
        self.simple_algo_data = AlgoSerializer(instance=self.simple_algo).data
        self.aggregate_algo_data = AlgoSerializer(instance=self.aggregate_algo).data
        self.composite_algo_data = AlgoSerializer(instance=self.composite_algo).data
        self.predict_algo_data = AlgoSerializer(instance=self.predict_algo).data
        self.metric_algo_data = AlgoSerializer(instance=self.metric_algo).data
        self.data_manager_data = DataManagerSerializer(instance=self.data_manager).data
        self.data_sample_data = DataSampleSerializer(instance=self.data_sample).data
        self.data_sample_data["data_manager_keys"] = [str(key) for key in self.data_sample_data["data_manager_keys"]]
        self.train_model_data = ModelSerializer(instance=self.train_model).data
        self.local_model_data = ModelSerializer(instance=self.local_model).data
        self.shared_model_data = ModelSerializer(instance=self.shared_model).data

        self.prepare_inputs()
        self.prepare_outputs()

    def prepare_inputs(self):
        self.datasamples_input = {
            "identifier": "datasamples",
            "asset_key": str(self.data_sample.key),
            "parent_task_key": None,
            "parent_task_output_identifier": None,
        }
        self.opener_input = {
            "identifier": "opener",
            "asset_key": str(self.data_manager.key),
            "parent_task_key": None,
            "parent_task_output_identifier": None,
        }
        self.opener_input_with_value = {**self.opener_input}
        self.opener_input_with_value["addressable"] = self.data_manager_data["opener"]
        self.opener_input_with_value["permissions"] = self.data_manager_data["permissions"]
        self.model_input = {
            "identifier": "model",
            "asset_key": None,
            "parent_task_key": str(self.done_train_task.key),
            "parent_task_output_identifier": "model",
        }
        self.model_input_with_value = {**self.model_input}
        self.model_input_with_value["addressable"] = self.train_model_data["address"]
        self.model_input_with_value["permissions"] = self.train_model_data["permissions"]
        self.models_input = {
            "identifier": "models",
            "asset_key": None,
            "parent_task_key": str(self.done_train_task.key),
            "parent_task_output_identifier": "model",
        }
        self.models_input_with_value = {**self.models_input}
        self.models_input_with_value["addressable"] = self.train_model_data["address"]
        self.models_input_with_value["permissions"] = self.train_model_data["permissions"]
        self.shared_input = {
            "identifier": "shared",
            "asset_key": None,
            "parent_task_key": str(self.done_train_task.key),
            "parent_task_output_identifier": "model",
        }
        self.shared_input_with_value = {**self.shared_input}
        self.shared_input_with_value["addressable"] = self.train_model_data["address"]
        self.shared_input_with_value["permissions"] = self.train_model_data["permissions"]
        self.predictions_input = {
            "identifier": "predictions",
            "asset_key": None,
            "parent_task_key": str(self.done_train_task.key),
            "parent_task_output_identifier": "model",
        }
        self.predictions_input_with_value = {**self.predictions_input}
        self.predictions_input_with_value["addressable"] = self.train_model_data["address"]
        self.predictions_input_with_value["permissions"] = self.train_model_data["permissions"]

    def prepare_outputs(self):
        self.model_output = {
            "permissions": {
                "download": {"authorized_ids": ["MyOrg1MSP"], "public": False},
                "process": {"authorized_ids": ["MyOrg1MSP"], "public": False},
            },
            "transient": False,
            "value": None,
        }
        self.model_output_with_value = {**self.model_output}
        self.model_output_with_value["value"] = self.train_model_data
        self.predictions_output = {
            "permissions": {
                "process": {"public": False, "authorized_ids": ["MyOrg1MSP"]},
                "download": {"public": False, "authorized_ids": ["MyOrg1MSP"]},
            },
            "transient": False,
            "value": None,
        }
        self.performance_output = {
            "permissions": {
                "download": {"authorized_ids": ["MyOrg1MSP"], "public": False},
                "process": {"authorized_ids": ["MyOrg1MSP"], "public": False},
            },
            "transient": False,
            "value": None,
        }
        self.performance_output_with_value = {**self.performance_output}
        self.performance_output_with_value["value"] = self.performance.value
        self.local_output = {
            "permissions": {
                "download": {"authorized_ids": ["MyOrg1MSP"], "public": False},
                "process": {"authorized_ids": ["MyOrg1MSP"], "public": False},
            },
            "transient": False,
            "value": None,
        }
        self.local_output_with_value = {**self.local_output}
        self.local_output_with_value["value"] = self.local_model_data
        self.shared_output = {
            "permissions": {
                "download": {"authorized_ids": ["MyOrg1MSP"], "public": False},
                "process": {"authorized_ids": ["MyOrg1MSP"], "public": False},
            },
            "transient": False,
            "value": None,
        }
        self.shared_output_with_value = {**self.shared_output}
        self.shared_output_with_value["value"] = self.shared_model_data

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class TaskBulkCreateViewTests(ComputeTaskViewTests):
    def test_task_bulk_create(self):
        def mock_register_compute_task(orc_request):
            """Build orchestrator register response from request data."""
            res = []
            for in_data in orc_request["tasks"]:
                extra_data_field = EXTRA_DATA_FIELD[in_data["category"]]
                out_data = {
                    "key": in_data["key"],
                    "category": in_data["category"],
                    "algo_key": in_data["algo_key"],
                    "compute_plan_key": in_data["compute_plan_key"],
                    "parent_task_keys": [],
                    "rank": 0,
                    "status": "STATUS_WAITING",
                    "owner": "MyOrg1MSP",
                    "worker": "MyOrg1MSP",
                    "inputs": in_data["inputs"],
                    "outputs": {
                        identifier: {
                            "permissions": {
                                "download": output["permissions"],
                                "process": output["permissions"],
                            },
                            "transient": output.get("transient", False),
                        }
                        for identifier, output in in_data["outputs"].items()
                    },
                    "creation_date": "2021-11-04T13:54:09.882662Z",
                    extra_data_field: in_data[extra_data_field],
                    "metadata": in_data["metadata"],
                    "logs_permission": {
                        "public": False,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                }
                res.append(out_data)
            return res

        train_task_key = str(uuid.uuid4())
        aggregate_task_key = str(uuid.uuid4())
        test_task_key = str(uuid.uuid4())
        predict_task_key = str(uuid.uuid4())
        data = {
            "tasks": [
                {
                    "compute_plan_key": self.compute_plan.key,
                    "category": "TASK_TRAIN",
                    "key": train_task_key,
                    "algo_key": self.simple_algo.key,
                    "data_manager_key": self.data_manager.key,
                    "train_data_sample_keys": [self.data_sample.key],
                    "inputs": [self.datasamples_input, self.opener_input, self.model_input],
                    "outputs": {
                        "model": {
                            "permissions": {"public": False, "authorized_ids": ["MyOrg1MSP"]},
                            "transient": False,
                        },
                    },
                },
                {
                    "compute_plan_key": self.compute_plan.key,
                    "category": "TASK_AGGREGATE",
                    "key": aggregate_task_key,
                    "in_models_keys": [train_task_key, self.done_train_task.key],
                    "algo_key": self.aggregate_algo.key,
                    "worker": "MyOrg1MSP",
                    "inputs": [self.models_input],
                    "outputs": {
                        "model": {"permissions": {"public": False, "authorized_ids": ["MyOrg1MSP"]}},
                    },
                },
                {
                    "compute_plan_key": self.compute_plan.key,
                    "category": "TASK_PREDICT",
                    "traintuple_key": train_task_key,
                    "key": predict_task_key,
                    "algo_key": self.predict_algo.key,
                    "data_manager_key": self.data_manager.key,
                    "test_data_sample_keys": [self.data_sample.key],
                    "inputs": [self.datasamples_input, self.opener_input, self.model_input, self.shared_input],
                    "outputs": {
                        "predictions": {"permissions": {"public": False, "authorized_ids": ["MyOrg1MSP"]}},
                    },
                },
                {
                    "compute_plan_key": self.compute_plan.key,
                    "category": "TASK_TEST",
                    "key": test_task_key,
                    "predicttuple_key": predict_task_key,
                    "algo_key": self.metric_algo.key,
                    "data_manager_key": self.data_manager.key,
                    "test_data_sample_keys": [self.data_sample.key],
                    "inputs": [self.datasamples_input, self.opener_input, self.predictions_input],
                    "outputs": {
                        "performance": {"permissions": {"public": False, "authorized_ids": ["MyOrg1MSP"]}},
                    },
                },
            ]
        }

        expected_response = [
            {
                "key": train_task_key,
                "algo": self.simple_algo_data,
                "category": "TASK_TRAIN",
                "compute_plan_key": str(self.compute_plan.key),
                "creation_date": "2021-11-04T13:54:09.882662Z",
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "authorized_ids": ["MyOrg1MSP"],
                    "public": False,
                },
                "metadata": {
                    TAG_KEY: "",
                },
                "owner": "MyOrg1MSP",
                "parent_task_keys": [],
                "rank": 0,
                "start_date": None,
                "status": "STATUS_WAITING",
                "tag": None,
                "train": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "model_permissions": {
                        "process": {"public": False, "authorized_ids": ["MyOrg1MSP"]},
                        "download": {"public": False, "authorized_ids": ["MyOrg1MSP"]},
                    },
                    "models": None,
                },
                "worker": "MyOrg1MSP",
                "inputs": [
                    self.datasamples_input,
                    self.opener_input_with_value,
                    self.model_input_with_value,
                ],
                "outputs": {
                    "model": self.model_output,
                },
            },
            {
                "key": aggregate_task_key,
                "algo": self.aggregate_algo_data,
                "category": "TASK_AGGREGATE",
                "compute_plan_key": str(self.compute_plan.key),
                "creation_date": "2021-11-04T13:54:09.882662Z",
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "authorized_ids": ["MyOrg1MSP"],
                    "public": False,
                },
                "metadata": {
                    TAG_KEY: "",
                },
                "owner": "MyOrg1MSP",
                "parent_task_keys": [],
                "rank": 0,
                "start_date": None,
                "status": "STATUS_WAITING",
                "tag": None,
                "aggregate": {
                    "model_permissions": {
                        "process": {"public": False, "authorized_ids": ["MyOrg1MSP"]},
                        "download": {"public": False, "authorized_ids": ["MyOrg1MSP"]},
                    },
                    "models": None,
                },
                "worker": "MyOrg1MSP",
                "inputs": [self.models_input_with_value],
                "outputs": {
                    "model": self.model_output,
                },
            },
            {
                "key": predict_task_key,
                "algo": self.predict_algo_data,
                "category": "TASK_PREDICT",
                "compute_plan_key": str(self.compute_plan.key),
                "creation_date": "2021-11-04T13:54:09.882662Z",
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "authorized_ids": ["MyOrg1MSP"],
                    "public": False,
                },
                "metadata": {
                    TAG_KEY: "",
                },
                "owner": "MyOrg1MSP",
                "parent_task_keys": [],
                "rank": 0,
                "start_date": None,
                "status": "STATUS_WAITING",
                "tag": None,
                "predict": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "prediction_permissions": {
                        "process": {"public": False, "authorized_ids": ["MyOrg1MSP"]},
                        "download": {"public": False, "authorized_ids": ["MyOrg1MSP"]},
                    },
                    "models": None,
                },
                "worker": "MyOrg1MSP",
                "inputs": [
                    self.datasamples_input,
                    self.opener_input_with_value,
                    self.model_input_with_value,
                    self.shared_input_with_value,
                ],
                "outputs": {
                    "predictions": self.predictions_output,
                },
            },
            {
                "key": test_task_key,
                "algo": self.metric_algo_data,
                "category": "TASK_TEST",
                "compute_plan_key": str(self.compute_plan.key),
                "creation_date": "2021-11-04T13:54:09.882662Z",
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "authorized_ids": ["MyOrg1MSP"],
                    "public": False,
                },
                "metadata": {
                    TAG_KEY: "",
                },
                "owner": "MyOrg1MSP",
                "parent_task_keys": [],
                "rank": 0,
                "start_date": None,
                "status": "STATUS_WAITING",
                "tag": None,
                "test": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "perfs": None,
                },
                "worker": "MyOrg1MSP",
                "inputs": [
                    self.datasamples_input,
                    self.opener_input_with_value,
                    self.predictions_input_with_value,
                ],
                "outputs": {
                    "performance": self.performance_output,
                },
            },
        ]

        url = reverse("api:task-bulk_create")
        with mock.patch.object(OrchestratorClient, "register_tasks", side_effect=mock_register_compute_task):
            response = self.client.post(url, data=data, format="json", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.json(), expected_response)


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class TrainTaskViewTests(ComputeTaskViewTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("api:traintuple-list")
        train_tasks = self.compute_tasks[ComputeTask.Category.TASK_TRAIN]
        todo_train_task = train_tasks[ComputeTask.Status.STATUS_TODO]
        waiting_train_task = train_tasks[ComputeTask.Status.STATUS_WAITING]
        doing_train_task = train_tasks[ComputeTask.Status.STATUS_DOING]
        done_train_task = train_tasks[ComputeTask.Status.STATUS_DONE]
        failed_train_task = train_tasks[ComputeTask.Status.STATUS_FAILED]
        canceled_train_task = train_tasks[ComputeTask.Status.STATUS_CANCELED]
        self.expected_results = [
            {
                "key": str(todo_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_TODO",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": todo_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "train": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "model_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,  # because start_date is None
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output},
            },
            {
                "key": str(waiting_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_WAITING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": waiting_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "train": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "model_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,  # because start_date is None
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output},
            },
            {
                "key": str(doing_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DOING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": doing_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": doing_train_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": None,
                "error_type": None,
                "train": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "model_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output},
            },
            {
                "key": str(done_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DONE",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": done_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": done_train_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": done_train_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "train": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "model_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": [self.train_model_data],
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output_with_value},
            },
            {
                "key": str(failed_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_FAILED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": failed_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": failed_train_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": failed_train_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": "EXECUTION_ERROR",
                "train": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "model_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output},
            },
            {
                "key": str(canceled_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_CANCELED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": canceled_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": canceled_train_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": canceled_train_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "train": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "model_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output},
            },
        ]

    def test_traintask_list_empty(self):
        Model.objects.filter(compute_task__category=ComputeTask.Category.TASK_TRAIN).delete()
        ComputeTask.objects.filter(category=ComputeTask.Category.TASK_TRAIN).delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_traintask_list_success(self):
        response = self.client.get(self.url, **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_traintask_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("api.views.computetask.ComputeTaskViewSet.list", side_effect=Exception("Unexpected error"))
    def test_traintask_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_traintask_list_filter(self):
        """Filter traintask on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_traintask_list_filter_and(self):
        """Filter traintask on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"key": key, "owner": owner})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_traintask_list_filter_in(self):
        """Filter traintask in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    @parameterized.expand(
        [
            ("STATUS_WAITING",),
            ("STATUS_TODO",),
            ("STATUS_DOING",),
            ("STATUS_DONE",),
            ("STATUS_CANCELED",),
            ("STATUS_FAILED",),
            ("STATUS_XXX",),
        ]
    )
    def test_traintask_list_filter_by_status(self, t_status):
        """Filter traintask on status."""
        filtered_train_tasks = [task for task in self.expected_results if task["status"] == t_status]
        params = urlencode({"status": t_status})
        response = self.client.get(f"{self.url}?{params}", **self.extra)

        if t_status != "STATUS_XXX":
            if t_status == ComputeTask.Status.STATUS_DOING:
                # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
                # couldn't be properly mocked
                for task in response.json().get("results"):
                    if task["status"] == ComputeTask.Status.STATUS_DOING:
                        task["duration"] = 3600
            self.assertEqual(
                response.json(),
                {"count": len(filtered_train_tasks), "next": None, "previous": None, "results": filtered_train_tasks},
            )
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            (["STATUS_WAITING", "STATUS_TODO"],),
            (["STATUS_DOING", "STATUS_DONE"],),
            (["STATUS_CANCELED", "STATUS_FAILED", "STATUS_XXX"],),
        ]
    )
    def test_traintask_list_filter_by_status_in(self, t_statuses):
        """Filter traintask on status."""
        filtered_train_tasks = [task for task in self.expected_results if task["status"] in t_statuses]
        params = urlencode({"status": ",".join(t_statuses)})
        response = self.client.get(f"{self.url}?{params}", **self.extra)

        if "STATUS_XXX" not in t_statuses:
            if ComputeTask.Status.STATUS_DOING in t_statuses:
                # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
                # couldn't be properly mocked
                for task in response.json().get("results"):
                    if task["status"] == ComputeTask.Status.STATUS_DOING:
                        task["duration"] = 3600
            self.assertEqual(
                response.json(),
                {
                    "count": len(filtered_train_tasks),
                    "next": None,
                    "previous": None,
                    "results": filtered_train_tasks,
                },
            )
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_traintask_match(self):
        """Match traintask on part of the name."""
        key = self.expected_results[0]["key"]
        # we're using key[19:] because it returns something a string with one dash in the middle: XXXX-YYYYYYYYYYYY
        # this will be handled as 2 tokens, so items matching both XXXX and YYYYYYYYYYYY will be returned
        # this should be enough to guarantee that there will only be one matching task
        params = urlencode({"match": key[19:]})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_traintask_match_and_filter(self):
        """Match traintask with filter."""
        key = self.expected_results[0]["key"]
        params = urlencode({"match": key[19:]})
        params = urlencode(
            {
                "status": "STATUS_TODO",
                "match": key[19:],
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    @parameterized.expand(
        [
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_traintask_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in r["results"]:
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_traintask_cp_list_success(self):
        """List traintasks for a specific compute plan (CPtraintaskViewSet)."""
        url = reverse("api:compute_plan_traintuple-list", args=[self.compute_plan.key])
        response = self.client.get(url, **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_traintask_list_cross_assets_filters(self):
        """Filter traintask on other asset key such as compute_plan_key, algo_key dataset_key and data_sample_key"""
        # filter on asset keys
        params_list = [
            urlencode({"compute_plan_key": self.compute_plan.key}),
            urlencode({"algo_key": self.simple_algo.key}),
            urlencode({"dataset_key": self.data_manager.key}),
            urlencode({"data_sample_key": self.data_sample.key}),
        ]

        for params in params_list:
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on wrong key
        params = urlencode({"algo_key": self.data_manager.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(len(response.json().get("results")), 0)

    def test_traintask_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.expected_results),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.expected_results[::-1])

    def test_traintask_retrieve(self):
        url = reverse("api:traintuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        # patch expected results with extended data
        self.expected_results[0]["train"]["data_manager"] = self.data_manager_data
        self.expected_results[0]["parent_tasks"] = []
        self.assertEqual(response.json(), self.expected_results[0])

    def test_traintask_retrieve_wrong_channel(self):
        url = reverse("api:traintuple-detail", args=[self.expected_results[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @internal_server_error_on_exception()
    @mock.patch("api.views.computetask.ComputeTaskViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_traintask_retrieve_fail(self, _):
        url = reverse("api:traintuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class TestTaskViewTests(ComputeTaskViewTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("api:testtuple-list")
        test_tasks = self.compute_tasks[ComputeTask.Category.TASK_TEST]
        todo_test_task = test_tasks[ComputeTask.Status.STATUS_TODO]
        waiting_test_task = test_tasks[ComputeTask.Status.STATUS_WAITING]
        doing_test_task = test_tasks[ComputeTask.Status.STATUS_DOING]
        done_test_task = test_tasks[ComputeTask.Status.STATUS_DONE]
        failed_test_task = test_tasks[ComputeTask.Status.STATUS_FAILED]
        canceled_test_task = test_tasks[ComputeTask.Status.STATUS_CANCELED]
        self.expected_results = [
            {
                "key": str(todo_test_task.key),
                "category": "TASK_TEST",
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_TODO",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": todo_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "test": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "perfs": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output},
            },
            {
                "key": str(waiting_test_task.key),
                "category": "TASK_TEST",
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_WAITING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": waiting_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "test": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "perfs": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output},
            },
            {
                "key": str(doing_test_task.key),
                "category": "TASK_TEST",
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DOING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": doing_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": doing_test_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": None,
                "error_type": None,
                "test": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "perfs": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output},
            },
            {
                "key": str(done_test_task.key),
                "category": "TASK_TEST",
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DONE",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": done_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": done_test_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": done_test_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "test": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "perfs": {str(self.metric_algo.key): self.performance.value},
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output_with_value},
            },
            {
                "key": str(failed_test_task.key),
                "category": "TASK_TEST",
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_FAILED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": failed_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": failed_test_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": failed_test_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": "EXECUTION_ERROR",
                "test": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "perfs": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output},
            },
            {
                "key": str(canceled_test_task.key),
                "category": "TASK_TEST",
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_CANCELED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": canceled_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": canceled_test_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": canceled_test_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "test": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "perfs": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output},
            },
        ]

    def test_testtask_list_empty(self):
        Performance.objects.filter(compute_task__category=ComputeTask.Category.TASK_TEST).delete()
        ComputeTask.objects.filter(category=ComputeTask.Category.TASK_TEST).delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_testtask_list_success(self):
        response = self.client.get(self.url, **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_testtask_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("api.views.computetask.ComputeTaskViewSet.list", side_effect=Exception("Unexpected error"))
    def test_testtask_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_testtask_list_filter(self):
        """Filter testtask on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_testtask_list_filter_and(self):
        """Filter testtask on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"key": key, "owner": owner})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_testtask_list_filter_in(self):
        """Filter testtask in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    @parameterized.expand(
        [
            ("STATUS_WAITING",),
            ("STATUS_TODO",),
            ("STATUS_DOING",),
            ("STATUS_DONE",),
            ("STATUS_CANCELED",),
            ("STATUS_FAILED",),
            ("STATUS_XXX",),
        ]
    )
    def test_testtask_list_filter_by_status(self, t_status):
        """Filter testtask on status."""
        filtered_test_tasks = [task for task in self.expected_results if task["status"] == t_status]
        params = urlencode({"status": t_status})
        response = self.client.get(f"{self.url}?{params}", **self.extra)

        if t_status != "STATUS_XXX":
            if t_status == "STATUS_DOING":
                # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
                # couldn't be properly mocked
                for task in response.json().get("results"):
                    if task["status"] == ComputeTask.Status.STATUS_DOING:
                        task["duration"] = 3600
            self.assertEqual(
                response.json(),
                {"count": len(filtered_test_tasks), "next": None, "previous": None, "results": filtered_test_tasks},
            )
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_testtask_match(self):
        """Match testtask on part of the name."""
        key = self.expected_results[0]["key"]
        params = urlencode({"match": key[19:]})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_testtask_match_and_filter(self):
        """Match testtask with filter."""
        key = self.expected_results[0]["key"]
        params = urlencode({"match": key[19:]})
        params = urlencode(
            {
                "status": "STATUS_TODO",
                "match": key[19:],
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_testtask_list_cross_assets_filters(self):
        """Filter testtask on other asset key such as compute_plan_key, algo_key, dataset_key and data_sample_key"""
        # filter on asset keys
        params_list = [
            urlencode({"compute_plan_key": self.compute_plan.key}),
            urlencode({"algo_key": self.metric_algo.key}),
            urlencode({"dataset_key": self.data_manager.key}),
            urlencode({"data_sample_key": self.data_sample.key}),
        ]

        for params in params_list:
            response = self.client.get(f"{self.url}?{params}", **self.extra)
            # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
            # couldn't be properly mocked
            for task in response.json().get("results"):
                if task["status"] == ComputeTask.Status.STATUS_DOING:
                    task["duration"] = 3600
            self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on wrong key
        params = urlencode({"algo_key": self.compute_plan.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(len(response.json().get("results")), 0)

    @parameterized.expand(
        [
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_testtask_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in r.get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600

        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_testtask_cp_list_success(self):
        """List testtasks for a specific compute plan (CPtesttaskViewSet)."""
        url = reverse("api:compute_plan_testtuple-list", args=[self.compute_plan.key])
        response = self.client.get(url, **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_testtask_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.expected_results),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.expected_results[::-1])

    def test_testtask_retrieve(self):
        url = reverse("api:testtuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        # patch expected results with extended data
        self.expected_results[0]["test"]["data_manager"] = self.data_manager_data
        self.expected_results[0]["parent_tasks"] = []
        self.assertEqual(response.json(), self.expected_results[0])

    def test_testtask_retrieve_wrong_channel(self):
        url = reverse("api:testtuple-detail", args=[self.expected_results[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @internal_server_error_on_exception()
    @mock.patch("api.views.computetask.ComputeTaskViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_testtask_retrieve_fail(self, _):
        url = reverse("api:testtuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class CompositeTaskViewTests(ComputeTaskViewTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("api:composite_traintuple-list")
        composite_tasks = self.compute_tasks[ComputeTask.Category.TASK_COMPOSITE]
        todo_composite_task = composite_tasks[ComputeTask.Status.STATUS_TODO]
        waiting_composite_task = composite_tasks[ComputeTask.Status.STATUS_WAITING]
        doing_composite_task = composite_tasks[ComputeTask.Status.STATUS_DOING]
        done_composite_task = composite_tasks[ComputeTask.Status.STATUS_DONE]
        failed_composite_task = composite_tasks[ComputeTask.Status.STATUS_FAILED]
        canceled_composite_task = composite_tasks[ComputeTask.Status.STATUS_CANCELED]
        self.expected_results = [
            {
                "key": str(todo_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_TODO",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": todo_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "composite": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "head_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "trunk_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output, "shared": self.shared_output},
            },
            {
                "key": str(waiting_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_WAITING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": waiting_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "composite": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "head_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "trunk_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output, "shared": self.shared_output},
            },
            {
                "key": str(doing_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DOING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": doing_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": doing_composite_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": None,
                "error_type": None,
                "composite": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "head_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "trunk_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output, "shared": self.shared_output},
            },
            {
                "key": str(done_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DONE",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": done_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": done_composite_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": done_composite_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "composite": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "head_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "trunk_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": [self.local_model_data, self.shared_model_data],
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output_with_value, "shared": self.shared_output_with_value},
            },
            {
                "key": str(failed_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_FAILED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": failed_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": failed_composite_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": failed_composite_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": "EXECUTION_ERROR",
                "composite": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "head_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "trunk_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output, "shared": self.shared_output},
            },
            {
                "key": str(canceled_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_CANCELED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "parent_task_keys": [],
                "tag": "",
                "creation_date": canceled_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": canceled_composite_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": canceled_composite_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "composite": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "head_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "trunk_permissions": {
                        "process": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                        "download": {
                            "public": False,
                            "authorized_ids": ["MyOrg1MSP"],
                        },
                    },
                    "models": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output, "shared": self.shared_output},
            },
        ]

    def test_compositetask_list_empty(self):
        Model.objects.filter(compute_task__category=ComputeTask.Category.TASK_COMPOSITE).delete()
        ComputeTask.objects.filter(category=ComputeTask.Category.TASK_COMPOSITE).delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_compositetask_list_success(self):
        response = self.client.get(self.url, **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_compositetask_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("api.views.computetask.ComputeTaskViewSet.list", side_effect=Exception("Unexpected error"))
    def test_compositetask_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_compositetask_list_filter(self):
        """Filter compositetask on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_compositetask_list_filter_and(self):
        """Filter compositetask on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"key": key, "owner": owner})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_compositetask_list_filter_in(self):
        """Filter compositetask in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    @parameterized.expand(
        [
            (["STATUS_WAITING", "STATUS_TODO"],),
            (["STATUS_DOING", "STATUS_DONE"],),
            (["STATUS_CANCELED", "STATUS_FAILED", "STATUS_XXX"],),
        ]
    )
    def test_compositetask_list_filter_by_status_in(self, t_statuses):
        """Filter compositetask on status."""
        filtered_composite_tasks = [task for task in self.expected_results if task["status"] in t_statuses]
        params = urlencode({"status": ",".join(t_statuses)})
        response = self.client.get(f"{self.url}?{params}", **self.extra)

        if "STATUS_XXX" not in t_statuses:
            if "STATUS_DOING" in t_statuses:
                # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
                # couldn't be properly mocked
                for task in response.json().get("results"):
                    if task["status"] == ComputeTask.Status.STATUS_DOING:
                        task["duration"] = 3600
            self.assertEqual(
                response.json(),
                {
                    "count": len(filtered_composite_tasks),
                    "next": None,
                    "previous": None,
                    "results": filtered_composite_tasks,
                },
            )
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compositetask_match(self):
        """Match compositetask on part of the name."""
        key = self.expected_results[0]["key"]
        params = urlencode({"match": key[19:]})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_compositetask_list_cross_assets_filters(self):
        """Filter compositetask on other asset key such as compute_plan_key, algo_key dataset_key and data_sample_key"""
        # filter on asset keys
        params_list = [
            urlencode({"compute_plan_key": self.compute_plan.key}),
            urlencode({"algo_key": self.composite_algo.key}),
            urlencode({"dataset_key": self.data_manager.key}),
            urlencode({"data_sample_key": self.data_sample.key}),
        ]

        for params in params_list:
            response = self.client.get(f"{self.url}?{params}", **self.extra)
            # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
            # couldn't be properly mocked
            for task in response.json().get("results"):
                if task["status"] == ComputeTask.Status.STATUS_DOING:
                    task["duration"] = 3600
            self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on wrong key
        params = urlencode({"algo_key": self.data_manager.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(len(response.json().get("results")), 0)

    @parameterized.expand(
        [
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_compositetask_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        r = response.json()
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_compositetask_cp_list_success(self):
        """List compositetasks for a specific compute plan (CPcompositetaskViewSet)."""
        url = reverse("api:compute_plan_composite_traintuple-list", args=[self.compute_plan.key])
        response = self.client.get(url, **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_compositetask_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.expected_results),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.expected_results[::-1])

    def test_compositetask_retrieve(self):
        url = reverse("api:composite_traintuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        # patch expected results with extended data
        self.expected_results[0]["composite"]["data_manager"] = self.data_manager_data
        self.expected_results[0]["parent_tasks"] = []
        self.assertEqual(response.json(), self.expected_results[0])

    def test_compositetask_retrieve_wrong_channel(self):
        url = reverse("api:composite_traintuple-detail", args=[self.expected_results[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @internal_server_error_on_exception()
    @mock.patch("api.views.computetask.ComputeTaskViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_compositetask_retrieve_fail(self, _):
        url = reverse("api:composite_traintuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class GenericTaskViewTests(ComputeTaskViewTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("api:task-list")

        train_tasks = self.compute_tasks[ComputeTask.Category.TASK_TRAIN]
        todo_train_task = train_tasks[ComputeTask.Status.STATUS_TODO]
        waiting_train_task = train_tasks[ComputeTask.Status.STATUS_WAITING]
        doing_train_task = train_tasks[ComputeTask.Status.STATUS_DOING]
        done_train_task = train_tasks[ComputeTask.Status.STATUS_DONE]
        failed_train_task = train_tasks[ComputeTask.Status.STATUS_FAILED]
        canceled_train_task = train_tasks[ComputeTask.Status.STATUS_CANCELED]

        test_tasks = self.compute_tasks[ComputeTask.Category.TASK_TEST]
        todo_test_task = test_tasks[ComputeTask.Status.STATUS_TODO]
        waiting_test_task = test_tasks[ComputeTask.Status.STATUS_WAITING]
        doing_test_task = test_tasks[ComputeTask.Status.STATUS_DOING]
        done_test_task = test_tasks[ComputeTask.Status.STATUS_DONE]
        failed_test_task = test_tasks[ComputeTask.Status.STATUS_FAILED]

        canceled_test_task = test_tasks[ComputeTask.Status.STATUS_CANCELED]
        composite_tasks = self.compute_tasks[ComputeTask.Category.TASK_COMPOSITE]
        todo_composite_task = composite_tasks[ComputeTask.Status.STATUS_TODO]
        waiting_composite_task = composite_tasks[ComputeTask.Status.STATUS_WAITING]
        doing_composite_task = composite_tasks[ComputeTask.Status.STATUS_DOING]
        done_composite_task = composite_tasks[ComputeTask.Status.STATUS_DONE]
        failed_composite_task = composite_tasks[ComputeTask.Status.STATUS_FAILED]
        canceled_composite_task = composite_tasks[ComputeTask.Status.STATUS_CANCELED]

        self.expected_results = [
            {
                "key": str(todo_train_task.key),
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_TODO",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": todo_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,  # because start_date is None
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output},
            },
            {
                "key": str(waiting_train_task.key),
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_WAITING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": waiting_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,  # because start_date is None
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output},
            },
            {
                "key": str(doing_train_task.key),
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DOING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": doing_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": doing_train_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output},
            },
            {
                "key": str(done_train_task.key),
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DONE",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": done_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": done_train_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": done_train_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output_with_value},
            },
            {
                "key": str(failed_train_task.key),
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_FAILED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": failed_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": failed_train_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": failed_train_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": "EXECUTION_ERROR",
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output},
            },
            {
                "key": str(canceled_train_task.key),
                "algo": self.simple_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_CANCELED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": canceled_train_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": canceled_train_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": canceled_train_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"model": self.model_output},
            },
            {
                "key": str(todo_test_task.key),
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_TODO",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": todo_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output},
            },
            {
                "key": str(waiting_test_task.key),
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_WAITING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": waiting_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output},
            },
            {
                "key": str(doing_test_task.key),
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DOING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": doing_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": doing_test_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output},
            },
            {
                "key": str(done_test_task.key),
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DONE",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": done_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": done_test_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": done_test_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output_with_value},
            },
            {
                "key": str(failed_test_task.key),
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_FAILED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": failed_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": failed_test_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": failed_test_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": "EXECUTION_ERROR",
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output},
            },
            {
                "key": str(canceled_test_task.key),
                "algo": self.metric_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_CANCELED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": canceled_test_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": canceled_test_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": canceled_test_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"performance": self.performance_output},
            },
            {
                "key": str(todo_composite_task.key),
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_TODO",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": todo_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output, "shared": self.shared_output},
            },
            {
                "key": str(waiting_composite_task.key),
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_WAITING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": waiting_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output, "shared": self.shared_output},
            },
            {
                "key": str(doing_composite_task.key),
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DOING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": doing_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": doing_composite_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output, "shared": self.shared_output},
            },
            {
                "key": str(done_composite_task.key),
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DONE",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": done_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": done_composite_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": done_composite_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output_with_value, "shared": self.shared_output_with_value},
            },
            {
                "key": str(failed_composite_task.key),
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_FAILED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": failed_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": failed_composite_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": failed_composite_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": "EXECUTION_ERROR",
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output, "shared": self.shared_output},
            },
            {
                "key": str(canceled_composite_task.key),
                "algo": self.composite_algo_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_CANCELED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": canceled_composite_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": canceled_composite_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": canceled_composite_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
                "inputs": [self.datasamples_input, self.opener_input_with_value],
                "outputs": {"local": self.local_output, "shared": self.shared_output},
            },
        ]

    def test_task_list_success(self):
        response = self.client.get(self.url, **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_task_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("api.views.computetask.ComputeTaskViewSet.list", side_effect=Exception("Unexpected error"))
    def test_task_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_task_list_filter(self):
        """Filter task on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_task_list_filter_and(self):
        """Filter task on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"key": key, "owner": owner})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_task_list_filter_in(self):
        """Filter task in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    @parameterized.expand(
        [
            ("STATUS_WAITING",),
            ("STATUS_TODO",),
            ("STATUS_DOING",),
            ("STATUS_DONE",),
            ("STATUS_CANCELED",),
            ("STATUS_FAILED",),
            ("STATUS_XXX",),
        ]
    )
    def test_task_list_filter_by_status(self, t_status):
        """Filter task on status."""
        filtered_train_tasks = [task for task in self.expected_results if task["status"] == t_status]
        params = urlencode({"status": t_status})
        response = self.client.get(f"{self.url}?{params}", **self.extra)

        if t_status != "STATUS_XXX":
            if t_status == ComputeTask.Status.STATUS_DOING:
                # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
                # couldn't be properly mocked
                for task in response.json().get("results"):
                    if task["status"] == ComputeTask.Status.STATUS_DOING:
                        task["duration"] = 3600
            self.assertEqual(
                response.json(),
                {"count": len(filtered_train_tasks), "next": None, "previous": None, "results": filtered_train_tasks},
            )
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            (["STATUS_WAITING", "STATUS_TODO"],),
            (["STATUS_DOING", "STATUS_DONE"],),
            (["STATUS_CANCELED", "STATUS_FAILED", "STATUS_XXX"],),
        ]
    )
    def test_task_list_filter_by_status_in(self, t_statuses):
        """Filter task on status."""
        filtered_train_tasks = [task for task in self.expected_results if task["status"] in t_statuses]
        params = urlencode({"status": ",".join(t_statuses)})
        response = self.client.get(f"{self.url}?{params}", **self.extra)

        if "STATUS_XXX" not in t_statuses:
            if ComputeTask.Status.STATUS_DOING in t_statuses:
                # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
                # couldn't be properly mocked
                for task in response.json().get("results"):
                    if task["status"] == ComputeTask.Status.STATUS_DOING:
                        task["duration"] = 3600
            self.assertEqual(
                response.json(),
                {
                    "count": len(filtered_train_tasks),
                    "next": None,
                    "previous": None,
                    "results": filtered_train_tasks,
                },
            )
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_task_match(self):
        """Match task on part of the name."""
        key = self.expected_results[0]["key"]
        # we're using key[19:] because it returns something a string with one dash in the middle: XXXX-YYYYYYYYYYYY
        # this will be handled as 2 tokens, so items matching both XXXX and YYYYYYYYYYYY will be returned
        # this should be enough to guarantee that there will only be one matching task
        params = urlencode({"match": key[19:]})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_task_match_and_filter(self):
        """Match task with filter."""
        key = self.expected_results[0]["key"]
        params = urlencode({"match": key[19:]})
        params = urlencode(
            {
                "status": "STATUS_TODO",
                "match": key[19:],
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    @parameterized.expand(
        [
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_task_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in r["results"]:
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_task_cp_list_success(self):
        """List tasks for a specific compute plan (CPTaskViewSet)."""
        url = reverse("api:compute_plan_task-list", args=[self.compute_plan.key])
        response = self.client.get(url, **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_task_list_cross_assets_filters(self):
        """Filter task on other asset key such as compute_plan_key, algo_key dataset_key and data_sample_key"""
        # filter on asset keys
        params_list = [
            urlencode({"compute_plan_key": self.compute_plan.key}),
            urlencode({"algo_key": self.simple_algo.key}),
            urlencode({"dataset_key": self.data_manager.key}),
            urlencode({"data_sample_key": self.data_sample.key}),
        ]

        for params in params_list:
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on wrong key
        params = urlencode({"algo_key": self.data_manager.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(len(response.json().get("results")), 0)

    def test_task_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.expected_results),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.expected_results[::-1])

    def test_task_retrieve(self):
        url = reverse("api:task-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.expected_results[0])

    def test_task_retrieve_wrong_channel(self):
        url = reverse("api:task-detail", args=[self.expected_results[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @internal_server_error_on_exception()
    @mock.patch("api.views.computetask.ComputeTaskViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_task_retrieve_fail(self, _):
        url = reverse("api:task-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_task_list_input_assets(self):
        url = reverse("api:task-input_assets", args=[self.expected_results[3]["key"]])
        response = self.client.get(url, **self.extra)
        expected_results = [
            {
                "identifier": "datasamples",
                "kind": "ASSET_DATA_SAMPLE",
                "asset": self.data_sample_data,
            },
            {
                "identifier": "opener",
                "kind": "ASSET_DATA_MANAGER",
                "asset": self.data_manager_data,
            },
        ]
        self.assertEqual(
            response.json(),
            {"count": len(expected_results), "next": None, "previous": None, "results": expected_results},
        )

    def test_task_list_input_assets_filter(self):
        url = reverse("api:task-input_assets", args=[self.expected_results[3]["key"]])

        # base response should contain a datamanager and a datasample
        response = self.client.get(url, **self.extra)
        data = response.json()
        assert data["count"] == 2

        # single filter
        response = self.client.get(url, data={"kind": "ASSET_DATA_MANAGER"}, **self.extra)
        data = response.json()
        assert data["count"] == 1

        # multi filter
        response = self.client.get(url, data={"kind": "ASSET_DATA_MANAGER,ASSET_MODEL"}, **self.extra)
        data = response.json()
        assert data["count"] == 1

        # invalid filter
        response = self.client.get(url, data={"kind": "foo"}, **self.extra)
        data = response.json()
        assert data["count"] == 2

        # invalid multi filter
        response = self.client.get(url, data={"kind": "ASSET_DATA_MANAGER,foo"}, **self.extra)
        data = response.json()
        assert data["count"] == 2

    def test_task_list_output_assets(self):
        url = reverse("api:task-output_assets", args=[self.expected_results[3]["key"]])
        response = self.client.get(url, **self.extra)
        expected_results = [
            {
                "identifier": "model",
                "kind": "ASSET_MODEL",
                "asset": self.train_model_data,
            },
        ]
        self.assertEqual(
            response.json(),
            {"count": len(expected_results), "next": None, "previous": None, "results": expected_results},
        )

    def test_task_list_output_assets_filter(self):
        url = reverse("api:task-output_assets", args=[self.expected_results[3]["key"]])

        # base response should contain a model
        response = self.client.get(url, **self.extra)
        data = response.json()
        assert data["count"] == 1

        # single filter
        response = self.client.get(url, data={"kind": "ASSET_PERFORMANCE"}, **self.extra)
        data = response.json()
        assert data["count"] == 0

        # multi filter
        response = self.client.get(url, data={"kind": "ASSET_PERFORMANCE,ASSET_MODEL"}, **self.extra)
        data = response.json()
        assert data["count"] == 1

        # invalid filter
        response = self.client.get(url, data={"kind": "foo"}, **self.extra)
        data = response.json()
        assert data["count"] == 1

        # invalid multi filter
        response = self.client.get(url, data={"kind": "ASSET_PERFORMANCE,foo"}, **self.extra)
        data = response.json()
        assert data["count"] == 1

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

from localrep.models import Algo as AlgoRep
from localrep.models import ComputeTask as ComputeTaskRep
from localrep.models import Model as ModelRep
from localrep.models import Performance as PerformanceRep
from localrep.serializers import AlgoSerializer as AlgoRepSerializer
from localrep.serializers import DataManagerSerializer as DataManagerRepSerializer
from localrep.serializers import ModelSerializer as ModelRepSerializer
from orchestrator.client import OrchestratorClient
from substrapp.tests import factory
from substrapp.views.computetask import EXTRA_DATA_FIELD

from ..common import AuthenticatedClient
from ..common import internal_server_error_on_exception

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

        self.algo = factory.create_algo()
        self.metric = factory.create_algo(category=AlgoRep.Category.ALGO_METRIC)
        self.data_manager = factory.create_datamanager()
        self.data_sample = factory.create_datasample([self.data_manager])
        self.compute_plan = factory.create_computeplan()

        self.compute_tasks = {}
        for category in (
            ComputeTaskRep.Category.TASK_TRAIN,
            ComputeTaskRep.Category.TASK_TEST,
            ComputeTaskRep.Category.TASK_COMPOSITE,
        ):
            self.compute_tasks[category] = {}
            for _status in (
                ComputeTaskRep.Status.STATUS_TODO,
                ComputeTaskRep.Status.STATUS_WAITING,
                ComputeTaskRep.Status.STATUS_DOING,
                ComputeTaskRep.Status.STATUS_DONE,
                ComputeTaskRep.Status.STATUS_FAILED,
                ComputeTaskRep.Status.STATUS_CANCELED,
            ):
                metrics = error_type = None
                if _status == ComputeTaskRep.Status.STATUS_FAILED:
                    error_type = ComputeTaskRep.ErrorType.ERROR_TYPE_EXECUTION
                if category == ComputeTaskRep.Category.TASK_TEST:
                    metrics = [self.metric]
                self.compute_tasks[category][_status] = factory.create_computetask(
                    self.compute_plan,
                    self.algo,
                    metrics=metrics,
                    data_manager=self.data_manager,
                    data_samples=[self.data_sample.key],
                    category=category,
                    status=_status,
                    error_type=error_type,
                )

        done_train_task = self.compute_tasks[ComputeTaskRep.Category.TASK_TRAIN][ComputeTaskRep.Status.STATUS_DONE]
        self.simple_model = factory.create_model(done_train_task, category=ModelRep.Category.MODEL_SIMPLE)

        done_composite_task = self.compute_tasks[ComputeTaskRep.Category.TASK_COMPOSITE][
            ComputeTaskRep.Status.STATUS_DONE
        ]
        self.head_model = factory.create_model(done_composite_task, category=ModelRep.Category.MODEL_HEAD)

        done_failed_task = self.compute_tasks[ComputeTaskRep.Category.TASK_TEST][ComputeTaskRep.Status.STATUS_DONE]
        self.performance = factory.create_performance(done_failed_task, self.metric)

        # we don't explicit serialized relationships as this test module is focused on computetask
        self.algo_data = AlgoRepSerializer(instance=self.algo).data
        self.metric_data = AlgoRepSerializer(instance=self.metric).data
        self.data_manager_data = DataManagerRepSerializer(instance=self.data_manager).data
        self.simple_model_data = ModelRepSerializer(instance=self.simple_model).data
        self.head_model_data = ModelRepSerializer(instance=self.head_model).data

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
                    "algo": {
                        "key": in_data["algo_key"],
                    },
                    "compute_plan_key": in_data["compute_plan_key"],
                    "parent_task_keys": in_data["parent_task_keys"],
                    "rank": 0,
                    "status": "STATUS_WAITING",
                    "owner": "MyOrg1MSP",
                    "worker": "MyOrg1MSP",
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
        done_train_task = self.compute_tasks[ComputeTaskRep.Category.TASK_TRAIN][ComputeTaskRep.Status.STATUS_DONE]
        data = {
            "tasks": [
                {
                    "compute_plan_key": self.compute_plan.key,
                    "category": "TASK_TRAIN",
                    "key": train_task_key,
                    "algo_key": self.algo.key,
                    "data_manager_key": self.data_manager.key,
                    "train_data_sample_keys": [self.data_sample.key],
                },
                {
                    "compute_plan_key": self.compute_plan.key,
                    "category": "TASK_AGGREGATE",
                    "key": aggregate_task_key,
                    "in_models_keys": [train_task_key, done_train_task.key],
                    "algo_key": self.algo.key,
                    "worker": "MyOrg1MSP",
                },
                {
                    "compute_plan_key": self.compute_plan.key,
                    "category": "TASK_TEST",
                    "key": test_task_key,
                    "traintuple_key": train_task_key,
                    "metric_keys": [self.metric.key],
                    "data_manager_key": self.data_manager.key,
                    "test_data_sample_keys": [self.data_sample.key],
                },
            ]
        }

        expected_response = [
            {
                "key": train_task_key,
                "algo": self.algo_data,
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
                    "__tag__": "",
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
                        "download": {
                            "authorized_ids": None,
                            "public": None,
                        },
                        "process": {
                            "authorized_ids": None,
                            "public": None,
                        },
                    },
                    "models": None,
                },
                "worker": "MyOrg1MSP",
            },
            {
                "key": aggregate_task_key,
                "algo": self.algo_data,
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
                    "__tag__": "",
                },
                "owner": "MyOrg1MSP",
                "parent_task_keys": [train_task_key, str(done_train_task.key)],
                "rank": 0,
                "start_date": None,
                "status": "STATUS_WAITING",
                "tag": None,
                "aggregate": {
                    "model_permissions": {
                        "download": {
                            "authorized_ids": None,
                            "public": None,
                        },
                        "process": {
                            "authorized_ids": None,
                            "public": None,
                        },
                    },
                    "models": None,
                },
                "worker": "MyOrg1MSP",
            },
            {
                "key": test_task_key,
                "algo": self.algo_data,
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
                    "__tag__": "",
                },
                "owner": "MyOrg1MSP",
                "parent_task_keys": [train_task_key],
                "rank": 0,
                "start_date": None,
                "status": "STATUS_WAITING",
                "tag": None,
                "test": {
                    "data_manager_key": str(self.data_manager.key),
                    "data_sample_keys": [str(self.data_sample.key)],
                    "metric_keys": [str(self.metric.key)],
                    "perfs": None,
                },
                "worker": "MyOrg1MSP",
            },
        ]
        url = reverse("substrapp:task_bulk_create")
        with mock.patch.object(
            OrchestratorClient, "register_tasks", side_effect=mock_register_compute_task
        ), mock.patch("substrapp.views.computetask._get_task_outputs"):
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
        self.url = reverse("substrapp:traintuple-list")
        train_tasks = self.compute_tasks[ComputeTaskRep.Category.TASK_TRAIN]
        todo_train_task = train_tasks[ComputeTaskRep.Status.STATUS_TODO]
        waiting_train_task = train_tasks[ComputeTaskRep.Status.STATUS_WAITING]
        doing_train_task = train_tasks[ComputeTaskRep.Status.STATUS_DOING]
        done_train_task = train_tasks[ComputeTaskRep.Status.STATUS_DONE]
        failed_train_task = train_tasks[ComputeTaskRep.Status.STATUS_FAILED]
        canceled_train_task = train_tasks[ComputeTaskRep.Status.STATUS_CANCELED]
        self.expected_results = [
            {
                "key": str(todo_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.algo_data,
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
            },
            {
                "key": str(waiting_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.algo_data,
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
            },
            {
                "key": str(doing_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.algo_data,
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
            },
            {
                "key": str(done_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.algo_data,
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
                    "models": [self.simple_model_data],
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
            {
                "key": str(failed_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.algo_data,
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
            },
            {
                "key": str(canceled_train_task.key),
                "category": "TASK_TRAIN",
                "algo": self.algo_data,
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
            },
        ]

    def test_traintask_list_empty(self):
        ModelRep.objects.filter(compute_task__category=ComputeTaskRep.Category.TASK_TRAIN).delete()
        ComputeTaskRep.objects.filter(category=ComputeTaskRep.Category.TASK_TRAIN).delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_traintask_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_traintask_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computetask.ComputeTaskViewSet.list", side_effect=Exception("Unexpected error"))
    def test_traintask_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_traintask_list_search_filter(self):
        """Filter traintask on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"search": f"traintuple:key:{key}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_traintask_list_filter(self):
        """Filter traintask on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_traintask_list_search_filter_and(self):
        """Filter traintask on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"search": f"traintuple:key:{key},traintuple:owner:{owner}"})
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

    def test_traintask_list_search_filter_in(self):
        """Filter traintask in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"search": f"traintuple:key:{key_0},traintuple:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
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

    def test_traintask_list_search_filter_or(self):
        """Filter traintask on key_0 or key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"search": f"traintuple:key:{key_0}-OR-traintuple:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_traintask_list_search_filter_or_and(self):
        """Filter traintask on (key_0 and owner_0) or (key_1 and owner_1)."""
        key_0, owner_0 = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        key_1, owner_1 = self.expected_results[1]["key"], self.expected_results[1]["owner"]
        params = urlencode(
            {
                "search": (
                    f"traintuple:key:{key_0},traintuple:owner:{owner_0}"
                    f"-OR-traintuple:key:{key_1},traintuple:owner:{owner_1}"
                )
            }
        )
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
    def test_traintask_list_search_filter_by_status(self, t_status):
        """Filter traintask on status."""
        filtered_train_tasks = [task for task in self.expected_results if task["status"] == t_status]
        params = urlencode({"search": f"traintuple:status:{t_status}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)

        if t_status != "STATUS_XXX":
            self.assertEqual(
                response.json(),
                {"count": len(filtered_train_tasks), "next": None, "previous": None, "results": filtered_train_tasks},
            )
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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
            self.assertEqual(
                response.json(),
                {"count": len(filtered_train_tasks), "next": None, "previous": None, "results": filtered_train_tasks},
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

    def test_traintask_match_and_search_filter(self):
        """Match traintask with filter."""
        key = self.expected_results[0]["key"]
        params = urlencode({"match": key[19:]})
        params = urlencode(
            {
                "search": "traintuple:status:STATUS_TODO",
                "match": key[19:],
            }
        )
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
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_traintask_cp_list_success(self):
        """List traintasks for a specific compute plan (CPtraintaskViewSet)."""
        url = reverse("substrapp:compute_plan_traintuple-list", args=[self.compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_traintask_list_search_filter_cp_key(self):
        """Filter traintask on key."""
        params = urlencode({"search": f"traintuple:compute_plan_key:{self.compute_plan.key}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_traintask_list_filter_cp_key(self):
        """Filter traintask on key."""
        params = urlencode({"compute_plan_key": self.compute_plan.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_traintask_list_cross_assets_filters(self):
        """Filter traintask on other asset key such as compute_plan_key, algo_key dataset_key and data_sample_key"""
        # filter on compute_plan_key
        params = urlencode({"compute_plan_key": self.compute_plan.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on algo_key
        params = urlencode({"algo_key": self.algo.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on dataset_key
        params = urlencode({"dataset_key": self.data_manager.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on data_sample_key
        params = urlencode({"data_sample_key": self.data_sample.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

    def test_traintask_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results[::-1])

    def test_traintask_retrieve(self):
        url = reverse("substrapp:traintuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        # patch expected results with extended data
        self.expected_results[0]["train"]["data_manager"] = self.data_manager_data
        self.expected_results[0]["parent_tasks"] = []
        self.assertEqual(response.json(), self.expected_results[0])

    def test_traintask_retrieve_wrong_channel(self):
        url = reverse("substrapp:traintuple-detail", args=[self.expected_results[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computetask.ComputeTaskViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_traintask_retrieve_fail(self, _):
        url = reverse("substrapp:traintuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class TestTaskViewTests(ComputeTaskViewTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("substrapp:testtuple-list")
        test_tasks = self.compute_tasks[ComputeTaskRep.Category.TASK_TEST]
        todo_test_task = test_tasks[ComputeTaskRep.Status.STATUS_TODO]
        waiting_test_task = test_tasks[ComputeTaskRep.Status.STATUS_WAITING]
        doing_test_task = test_tasks[ComputeTaskRep.Status.STATUS_DOING]
        done_test_task = test_tasks[ComputeTaskRep.Status.STATUS_DONE]
        failed_test_task = test_tasks[ComputeTaskRep.Status.STATUS_FAILED]
        canceled_test_task = test_tasks[ComputeTaskRep.Status.STATUS_CANCELED]
        self.expected_results = [
            {
                "key": str(todo_test_task.key),
                "category": "TASK_TEST",
                "algo": self.algo_data,
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
                    "metric_keys": [str(self.metric.key)],
                    "perfs": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
            {
                "key": str(waiting_test_task.key),
                "category": "TASK_TEST",
                "algo": self.algo_data,
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
                    "metric_keys": [str(self.metric.key)],
                    "perfs": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
            {
                "key": str(doing_test_task.key),
                "category": "TASK_TEST",
                "algo": self.algo_data,
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
                    "metric_keys": [str(self.metric.key)],
                    "perfs": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
            {
                "key": str(done_test_task.key),
                "category": "TASK_TEST",
                "algo": self.algo_data,
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
                    "metric_keys": [str(self.metric.key)],
                    "perfs": {str(self.metric.key): self.performance.value},
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
            {
                "key": str(failed_test_task.key),
                "category": "TASK_TEST",
                "algo": self.algo_data,
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
                    "metric_keys": [str(self.metric.key)],
                    "perfs": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
            {
                "key": str(canceled_test_task.key),
                "category": "TASK_TEST",
                "algo": self.algo_data,
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
                    "metric_keys": [str(self.metric.key)],
                    "perfs": None,
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
        ]

    def test_testtask_list_empty(self):
        PerformanceRep.objects.filter(compute_task__category=ComputeTaskRep.Category.TASK_TEST).delete()
        ComputeTaskRep.objects.filter(category=ComputeTaskRep.Category.TASK_TEST).delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_testtask_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_testtask_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computetask.ComputeTaskViewSet.list", side_effect=Exception("Unexpected error"))
    def test_testtask_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_testtask_list_filter(self):
        """Filter testtask on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"search": f"testtuple:key:{key}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_testtask_list_filter_and(self):
        """Filter testtask on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"search": f"testtuple:key:{key},testtuple:owner:{owner}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_testtask_list_filter_in(self):
        """Filter testtask in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"search": f"testtuple:key:{key_0},testtuple:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_testtask_list_filter_or(self):
        """Filter testtask on key_0 or key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"search": f"testtuple:key:{key_0}-OR-testtuple:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_testtask_list_filter_or_and(self):
        """Filter testtask on (key_0 and owner_0) or (key_1 and owner_1)."""
        key_0, owner_0 = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        key_1, owner_1 = self.expected_results[1]["key"], self.expected_results[1]["owner"]
        params = urlencode(
            {
                "search": (
                    f"testtuple:key:{key_0},testtuple:owner:{owner_0}"
                    f"-OR-testtuple:key:{key_1},testtuple:owner:{owner_1}"
                )
            }
        )
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
    def test_testtask_list_filter_by_status(self, tt__status):
        """Filter testtask on status."""
        filtered_test_tasks = [task for task in self.expected_results if task["status"] == tt__status]
        params = urlencode({"search": f"testtuple:status:{tt__status}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        if tt__status != "STATUS_XXX":

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
                "search": "testtuple:status:STATUS_TODO",
                "match": key[19:],
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_testtask_list_cross_assets_filters(self):
        """Filter testtask on other asset key such as compute_plan_key, algo_key dataset_key and data_sample_key"""
        # filter on compute_plan_key
        params = urlencode({"compute_plan_key": self.compute_plan.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on algo_key
        params = urlencode({"algo_key": self.algo.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on dataset_key
        params = urlencode({"dataset_key": self.data_manager.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on data_sample_key
        params = urlencode({"data_sample_key": self.data_sample.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

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
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_testtask_cp_list_success(self):
        """List testtasks for a specific compute plan (CPtesttaskViewSet)."""
        url = reverse("substrapp:compute_plan_testtuple-list", args=[self.compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_testtask_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results[::-1])

    def test_testtask_retrieve(self):
        url = reverse("substrapp:testtuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        # patch expected results with extended data
        self.expected_results[0]["test"]["data_manager"] = self.data_manager_data
        self.expected_results[0]["test"]["metrics"] = [self.metric_data]
        self.expected_results[0]["parent_tasks"] = []
        self.assertEqual(response.json(), self.expected_results[0])

    def test_testtask_retrieve_wrong_channel(self):
        url = reverse("substrapp:testtuple-detail", args=[self.expected_results[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computetask.ComputeTaskViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_testtask_retrieve_fail(self, _):
        url = reverse("substrapp:testtuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class CompositeTaskViewTests(ComputeTaskViewTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("substrapp:composite_traintuple-list")
        composite_tasks = self.compute_tasks[ComputeTaskRep.Category.TASK_COMPOSITE]
        todo_composite_task = composite_tasks[ComputeTaskRep.Status.STATUS_TODO]
        waiting_composite_task = composite_tasks[ComputeTaskRep.Status.STATUS_WAITING]
        doing_composite_task = composite_tasks[ComputeTaskRep.Status.STATUS_DOING]
        done_composite_task = composite_tasks[ComputeTaskRep.Status.STATUS_DONE]
        failed_composite_task = composite_tasks[ComputeTaskRep.Status.STATUS_FAILED]
        canceled_composite_task = composite_tasks[ComputeTaskRep.Status.STATUS_CANCELED]
        self.expected_results = [
            {
                "key": str(todo_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.algo_data,
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
            },
            {
                "key": str(waiting_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.algo_data,
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
            },
            {
                "key": str(doing_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.algo_data,
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
            },
            {
                "key": str(done_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.algo_data,
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
                    "models": [self.head_model_data],
                },
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
            {
                "key": str(failed_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.algo_data,
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
            },
            {
                "key": str(canceled_composite_task.key),
                "category": "TASK_COMPOSITE",
                "algo": self.algo_data,
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
            },
        ]

    def test_compositetask_list_empty(self):
        ModelRep.objects.filter(compute_task__category=ComputeTaskRep.Category.TASK_COMPOSITE).delete()
        ComputeTaskRep.objects.filter(category=ComputeTaskRep.Category.TASK_COMPOSITE).delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_compositetask_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_compositetask_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computetask.ComputeTaskViewSet.list", side_effect=Exception("Unexpected error"))
    def test_compositetask_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_compositetask_list_filter(self):
        """Filter compositetask on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"search": f"composite_traintuple:key:{key}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_compositetask_list_filter_and(self):
        """Filter compositetask on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"search": f"composite_traintuple:key:{key},composite_traintuple:owner:{owner}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_compositetask_list_filter_in(self):
        """Filter compositetask in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"search": f"composite_traintuple:key:{key_0},composite_traintuple:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_compositetask_list_filter_or(self):
        """Filter compositetask on key_0 or key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"search": f"composite_traintuple:key:{key_0}-OR-composite_traintuple:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_compositetask_list_filter_or_and(self):
        """Filter compositetask on (key_0 and owner_0) or (key_1 and owner_1)."""
        key_0, owner_0 = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        key_1, owner_1 = self.expected_results[1]["key"], self.expected_results[1]["owner"]
        params = urlencode(
            {
                "search": (
                    f"composite_traintuple:key:{key_0},composite_traintuple:owner:{owner_0}"
                    f"-OR-composite_traintuple:key:{key_1},composite_traintuple:owner:{owner_1}"
                )
            }
        )
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
    def test_compositetask_list_filter_by_status(self, t_status):
        """Filter compositetask on status."""
        filtered_composite_tasks = [task for task in self.expected_results if task["status"] == t_status]
        params = urlencode({"search": f"composite_traintuple:status:{t_status}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)

        if t_status != "STATUS_XXX":
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

    def test_compositetask_match_and_filter(self):
        """Match compositetask with filter."""
        key = self.expected_results[0]["key"]
        params = urlencode({"match": key[19:]})
        params = urlencode(
            {
                "search": "composite_traintuple:status:STATUS_TODO",
                "match": key[19:],
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_compositetask_list_cross_assets_filters(self):
        """Filter compositetask on other asset key such as compute_plan_key, algo_key dataset_key and data_sample_key"""
        # filter on compute_plan_key
        params = urlencode({"compute_plan_key": self.compute_plan.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on algo_key
        params = urlencode({"algo_key": self.algo.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on dataset_key
        params = urlencode({"dataset_key": self.data_manager.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

        # filter on data_sample_key
        params = urlencode({"data_sample_key": self.data_sample.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

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
        r = response.json()
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_compositetask_cp_list_success(self):
        """List compositetasks for a specific compute plan (CPcompositetaskViewSet)."""
        url = reverse("substrapp:compute_plan_composite_traintuple-list", args=[self.compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_compositetask_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results[::-1])

    def test_compositetask_retrieve(self):
        url = reverse("substrapp:composite_traintuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        # patch expected results with extended data
        self.expected_results[0]["composite"]["data_manager"] = self.data_manager_data
        self.expected_results[0]["parent_tasks"] = []
        self.assertEqual(response.json(), self.expected_results[0])

    def test_compositetask_retrieve_wrong_channel(self):
        url = reverse("substrapp:composite_traintuple-detail", args=[self.expected_results[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computetask.ComputeTaskViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_compositetask_retrieve_fail(self, _):
        url = reverse("substrapp:composite_traintuple-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

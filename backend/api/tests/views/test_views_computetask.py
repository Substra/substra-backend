import logging
import os
import shutil
import tempfile
import uuid
from unittest import mock

import pytest
from django.db import connection
from django.test import override_settings
from django.test import utils
from django.urls import reverse
from django.utils.http import urlencode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import ComputeTask
from api.serializers import DataManagerSerializer
from api.serializers import DataSampleSerializer
from api.serializers import FunctionSerializer
from api.serializers import ModelSerializer
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient
from api.tests.common import internal_server_error_on_exception
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

        self.simple_function = factory.create_function(
            inputs=factory.build_function_inputs(["datasamples", "opener", "model"]),
            outputs=factory.build_function_outputs(["model"]),
            name="simple function",
        )
        self.data_manager = factory.create_datamanager()
        self.data_sample = factory.create_datasample([self.data_manager])
        self.compute_plan = factory.create_computeplan()

        self.compute_tasks = {}
        input_keys = {
            "opener": [self.data_manager.key],
            "datasamples": [self.data_sample.key],
        }

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
            self.compute_tasks[_status] = factory.create_computetask(
                self.compute_plan,
                self.simple_function,
                inputs=factory.build_computetask_inputs(self.simple_function, input_keys),
                outputs=factory.build_computetask_outputs(self.simple_function),
                data_manager=self.data_manager,
                data_samples=[self.data_sample.key],
                status=_status,
                error_type=error_type,
            )
        self.done_task = self.compute_tasks[ComputeTask.Status.STATUS_DONE]
        self.model = factory.create_model(self.done_task, identifier="model")

        # we don't explicitly serialize relationships as this test module is focused on computetask
        self.simple_function_data = FunctionSerializer(instance=self.simple_function).data
        self.data_manager_data = DataManagerSerializer(instance=self.data_manager).data
        self.data_sample_data = DataSampleSerializer(instance=self.data_sample).data
        self.data_sample_data["data_manager_keys"] = [str(key) for key in self.data_sample_data["data_manager_keys"]]
        self.model_data = ModelSerializer(instance=self.model).data

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
            "parent_task_key": str(self.done_task.key),
            "parent_task_output_identifier": "model",
        }
        self.model_input_with_value = {**self.model_input}
        self.model_input_with_value["addressable"] = self.model_data["address"]
        self.model_input_with_value["permissions"] = self.model_data["permissions"]
        self.models_input = {
            "identifier": "models",
            "asset_key": None,
            "parent_task_key": str(self.done_task.key),
            "parent_task_output_identifier": "model",
        }
        self.models_input_with_value = {**self.models_input}
        self.models_input_with_value["addressable"] = self.model_data["address"]
        self.models_input_with_value["permissions"] = self.model_data["permissions"]
        self.shared_input = {
            "identifier": "shared",
            "asset_key": None,
            "parent_task_key": str(self.done_task.key),
            "parent_task_output_identifier": "model",
        }
        self.shared_input_with_value = {**self.shared_input}
        self.shared_input_with_value["addressable"] = self.model_data["address"]
        self.shared_input_with_value["permissions"] = self.model_data["permissions"]
        self.predictions_input = {
            "identifier": "predictions",
            "asset_key": None,
            "parent_task_key": str(self.done_task.key),
            "parent_task_output_identifier": "model",
        }
        self.predictions_input_with_value = {**self.predictions_input}
        self.predictions_input_with_value["addressable"] = self.model_data["address"]
        self.predictions_input_with_value["permissions"] = self.model_data["permissions"]

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
        self.model_output_with_value["value"] = self.model_data
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
                out_data = {
                    "key": in_data["key"],
                    "function_key": in_data["function_key"],
                    "compute_plan_key": in_data["compute_plan_key"],
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
                    "metadata": in_data["metadata"],
                    "logs_permission": {
                        "public": False,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                }
                res.append(out_data)
            return res

        train_task_key = str(uuid.uuid4())
        data = {
            "tasks": [
                {
                    "compute_plan_key": self.compute_plan.key,
                    "key": train_task_key,
                    "function_key": self.simple_function.key,
                    "inputs": [self.datasamples_input, self.opener_input, self.model_input],
                    "outputs": {
                        "model": {
                            "permissions": {"public": False, "authorized_ids": ["MyOrg1MSP"]},
                            "transient": False,
                        },
                    },
                },
            ]
        }

        expected_response = [
            {
                "key": train_task_key,
                "function": self.simple_function_data,
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
                "rank": 0,
                "start_date": None,
                "status": "STATUS_WAITING",
                "tag": None,
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
        ]

        url = reverse("api:task-bulk_create")
        with mock.patch.object(OrchestratorClient, "register_tasks", side_effect=mock_register_compute_task):
            response = self.client.post(url, data=data, format="json", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        assert response.json()[0] == expected_response[0]
        self.assertEqual(response.json(), expected_response)


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class GenericTaskViewTests(ComputeTaskViewTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("api:task-list")

        todo_task = self.compute_tasks[ComputeTask.Status.STATUS_TODO]
        waiting_task = self.compute_tasks[ComputeTask.Status.STATUS_WAITING]
        doing_task = self.compute_tasks[ComputeTask.Status.STATUS_DOING]
        done_task = self.compute_tasks[ComputeTask.Status.STATUS_DONE]
        failed_task = self.compute_tasks[ComputeTask.Status.STATUS_FAILED]
        canceled_task = self.compute_tasks[ComputeTask.Status.STATUS_CANCELED]

        self.detail_expected_results = {
            "key": str(todo_task.key),
            "function": self.simple_function_data,
            "owner": "MyOrg1MSP",
            "compute_plan_key": str(self.compute_plan.key),
            "metadata": {},
            "status": "STATUS_TODO",
            "worker": "MyOrg1MSP",
            "rank": 1,
            "tag": "",
            "creation_date": todo_task.creation_date.isoformat().replace("+00:00", "Z"),
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
        }

        self.list_expected_results = [
            {
                "key": str(todo_task.key),
                "function": self.simple_function_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_TODO",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": todo_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,  # because start_date is None
            },
            {
                "key": str(waiting_task.key),
                "function": self.simple_function_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_WAITING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": waiting_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 0,  # because start_date is None
            },
            {
                "key": str(doing_task.key),
                "function": self.simple_function_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DOING",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": doing_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": doing_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": None,
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
            },
            {
                "key": str(done_task.key),
                "function": self.simple_function_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_DONE",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": done_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": done_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": done_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
            },
            {
                "key": str(failed_task.key),
                "function": self.simple_function_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_FAILED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": failed_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": failed_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": failed_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": "EXECUTION_ERROR",
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
            },
            {
                "key": str(canceled_task.key),
                "function": self.simple_function_data,
                "owner": "MyOrg1MSP",
                "compute_plan_key": str(self.compute_plan.key),
                "metadata": {},
                "status": "STATUS_CANCELED",
                "worker": "MyOrg1MSP",
                "rank": 1,
                "tag": "",
                "creation_date": canceled_task.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": canceled_task.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": canceled_task.end_date.isoformat().replace("+00:00", "Z"),
                "error_type": None,
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "duration": 3600,
            },
        ]

        self.done_task_key = done_task.key

    def test_task_list_success(self):
        response = self.client.get(self.url, **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(
            response.json(),
            {
                "count": len(self.list_expected_results),
                "next": None,
                "previous": None,
                "results": self.list_expected_results,
            },
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
        key = self.list_expected_results[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.list_expected_results[:1]}
        )

    def test_task_list_filter_and(self):
        """Filter task on key and owner."""
        key, owner = self.list_expected_results[0]["key"], self.list_expected_results[0]["owner"]
        params = urlencode({"key": key, "owner": owner})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.list_expected_results[:1]}
        )

    def test_task_list_filter_in(self):
        """Filter task in key_0, key_1."""
        key_0 = self.list_expected_results[0]["key"]
        key_1 = self.list_expected_results[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.list_expected_results[:2]}
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
        filtered_train_tasks = [task for task in self.list_expected_results if task["status"] == t_status]
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
        filtered_train_tasks = [task for task in self.list_expected_results if task["status"] in t_statuses]
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
        key = self.list_expected_results[0]["key"]
        # we're using key[19:] because it returns something a string with one dash in the middle: XXXX-YYYYYYYYYYYY
        # this will be handled as 2 tokens, so items matching both XXXX and YYYYYYYYYYYY will be returned
        # this should be enough to guarantee that there will only be one matching task
        params = urlencode({"match": key[19:]})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.list_expected_results[:1]}
        )

    def test_task_match_and_filter(self):
        """Match task with filter."""
        key = self.list_expected_results[0]["key"]
        params = urlencode({"match": key[19:]})
        params = urlencode(
            {
                "status": "STATUS_TODO",
                "match": key[19:],
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.list_expected_results[:1]}
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
        self.assertEqual(r["count"], len(self.list_expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.list_expected_results[offset : offset + page_size])

    def test_task_cp_list_success(self):
        """List tasks for a specific compute plan (CPTaskViewSet)."""
        url = reverse("api:compute_plan_task-list", args=[self.compute_plan.key])
        response = self.client.get(url, **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600

        assert response.json() == {
            "count": len(self.list_expected_results),
            "next": None,
            "previous": None,
            "results": self.list_expected_results,
        }

    def test_task_list_cross_assets_filters(self):
        """Filter task on other asset key such as compute_plan_key, function_key dataset_key and data_sample_key"""
        # filter on asset keys
        params_list = [
            urlencode({"compute_plan_key": self.compute_plan.key}),
            urlencode({"function_key": self.simple_function.key}),
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
        self.assertEqual(response.json().get("results"), self.list_expected_results)

        # filter on wrong key
        params = urlencode({"function_key": self.data_manager.key})
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
        self.assertEqual(response.json().get("results"), self.list_expected_results),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing tasks as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for task in response.json().get("results"):
            if task["status"] == ComputeTask.Status.STATUS_DOING:
                task["duration"] = 3600
        self.assertEqual(response.json().get("results"), self.list_expected_results[::-1])

    def test_task_retrieve(self):
        url = reverse("api:task-detail", args=[self.detail_expected_results["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.detail_expected_results)

    def test_task_retrieve_wrong_channel(self):
        url = reverse("api:task-detail", args=[self.detail_expected_results["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @internal_server_error_on_exception()
    @mock.patch("api.views.computetask.ComputeTaskViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_task_retrieve_fail(self, _):
        url = reverse("api:task-detail", args=[self.detail_expected_results["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_task_list_input_assets(self):
        url = reverse("api:task-input_assets", args=[self.done_task_key])
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
        url = reverse("api:task-input_assets", args=[self.done_task_key])

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
        url = reverse("api:task-output_assets", args=[self.done_task_key])
        response = self.client.get(url, **self.extra)
        expected_results = [
            {
                "identifier": "model",
                "kind": "ASSET_MODEL",
                "asset": self.model_data,
            },
        ]
        self.assertEqual(
            response.json(),
            {"count": len(expected_results), "next": None, "previous": None, "results": expected_results},
        )

    def test_task_list_output_assets_filter(self):
        url = reverse("api:task-output_assets", args=[self.done_task_key])

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


@pytest.fixture
def create_compute_task():
    def _create_compute_task(compute_plan, n_data_sample=4):
        data_manager = factory.create_datamanager()
        data_samples = [factory.create_datasample([data_manager]) for _ in range(n_data_sample)]
        input_keys = {
            "opener": [data_manager.key],
            "datasamples": [data_sample.key for data_sample in data_samples],
        }
        function = factory.create_function(
            inputs=factory.build_function_inputs(["datasamples", "opener", "model"]),
            outputs=factory.build_function_outputs(["model"]),
            name="simple function",
        )
        return factory.create_computetask(
            compute_plan,
            function,
            inputs=factory.build_computetask_inputs(function, input_keys),
            outputs=factory.build_computetask_outputs(function),
            data_manager=data_manager,
            data_samples=[data_sample.key for data_sample in data_samples],
            status=ComputeTask.Status.STATUS_DONE,
        )

    return _create_compute_task


@pytest.fixture
def create_compute_plan(create_compute_task):
    def _create_compute_plan(n_task=20, n_data_sample=4):
        compute_plan = factory.create_computeplan()
        [create_compute_task(compute_plan, n_data_sample=n_data_sample) for _ in range(n_task)]
        return compute_plan

    return _create_compute_plan


@pytest.mark.django_db
def test_n_plus_one_queries_compute_task_in_compute_plan(authenticated_client, create_compute_plan):
    """
    The goal of this test is to check that the number of queries is in O(1), that is to say independent of the number
    of tasks in the list.
    Some queries are cached by Django, so we allow a bit of slack.
    """
    compute_plan_60 = create_compute_plan(n_task=60)

    url_60 = reverse("api:compute_plan_task-list", args=[compute_plan_60.key])

    with utils.CaptureQueriesContext(connection) as queries_60:
        authenticated_client.get(url_60)
    queries_for_60_tasks = len(queries_60.captured_queries)

    compute_plan_10 = create_compute_plan(n_task=10)

    url_10 = reverse("api:compute_plan_task-list", args=[compute_plan_10.key])

    with utils.CaptureQueriesContext(connection) as queries_10:
        authenticated_client.get(url_10)

    queries_for_10_tasks = len(queries_10.captured_queries)

    assert abs(queries_for_60_tasks - queries_for_10_tasks) < 5
    assert queries_for_60_tasks < 15


@pytest.mark.django_db
def test_n_plus_one_queries_compute_task_detail(authenticated_client, create_compute_task):
    """
    The goal of this test is to check that the number of queries is in O(1), that is to say independent of the number
    of inputs.
    Some queries are cached by Django, so we allow a bit of slack.
    """
    compute_plan = factory.create_computeplan()
    compute_task_4 = create_compute_task(compute_plan, n_data_sample=4)

    url_4 = reverse("api:task-detail", args=[compute_task_4.key])

    with utils.CaptureQueriesContext(connection) as queries_4:
        authenticated_client.get(url_4)
    queries_for_4_samples = len(queries_4.captured_queries)

    compute_task_10 = create_compute_task(compute_plan, n_data_sample=10)

    url_10 = reverse("api:task-detail", args=[compute_task_10.key])

    with utils.CaptureQueriesContext(connection) as queries_10:
        authenticated_client.get(url_10)
    queries_for_10_samples = len(queries_10.captured_queries)

    assert abs(queries_for_4_samples - queries_for_10_samples) < 5
    assert queries_for_4_samples < 20


@pytest.mark.django_db
def test_n_plus_one_queries_compute_task_list(authenticated_client, create_compute_task):
    """
    The goal of this test is to check that the number of queries is in O(1), that is to say independent of the number
    of tasks in the DB.
    Some queries are cached by Django, so we allow a bit of slack.
    """
    compute_plan = factory.create_computeplan()
    url = reverse("api:task-list")

    for _ in range(10):
        create_compute_task(compute_plan)

    with utils.CaptureQueriesContext(connection) as queries_10:
        authenticated_client.get(url)
    queries_for_10_tasks = len(queries_10.captured_queries)

    for _ in range(50):
        create_compute_task(compute_plan)

    with utils.CaptureQueriesContext(connection) as queries_60:
        authenticated_client.get(url)
    queries_for_60_tasks = len(queries_60.captured_queries)

    assert abs(queries_for_60_tasks - queries_for_10_tasks) < 5
    assert queries_for_60_tasks < 15

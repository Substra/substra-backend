import datetime
import json
import os
import shutil
import tempfile
import uuid
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from grpc import StatusCode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import ComputePlan as ComputePlanRep
from api.models import ComputeTask as ComputeTaskRep
from api.tests import asset_factory as factory
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from substrapp.tests.common import AuthenticatedClient
from substrapp.tests.common import internal_server_error_on_exception

MEDIA_ROOT = tempfile.mkdtemp()


def mock_register_compute_plan(data):
    """Build orchestrator register response from request data."""
    return {
        "key": data["key"],
        "tag": data["tag"],
        "name": data["name"],
        "metadata": data["metadata"],
        "delete_intermediary_models": data["delete_intermediary_models"],
        "status": ComputePlanRep.Status.PLAN_STATUS_TODO,
        "task_count": 0,
        "done_count": 0,
        "waiting_count": 0,
        "todo_count": 0,
        "doing_count": 0,
        "canceled_count": 0,
        "failed_count": 0,
        "owner": "MyOrg1MSP",
        "creation_date": "2021-11-04T13:54:09.882662Z",
    }


class AuthenticatedAPITestCase(APITestCase):
    client_class = AuthenticatedClient


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={
        "mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True},
        "yourchannel": {"chaincode": {"name": "yourcc"}, "model_export_enabled": True},
    },
)
class ComputePlanViewTests(AuthenticatedAPITestCase):
    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.maxDiff = None
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        self.url = reverse("api:compute_plan-list")

        algo = factory.create_algo()

        todo_cp = factory.create_computeplan(name="To do", status=ComputePlanRep.Status.PLAN_STATUS_TODO)
        factory.create_computetask(todo_cp, algo, status=ComputeTaskRep.Status.STATUS_TODO)

        doing_cp = factory.create_computeplan(name="Doing", status=ComputePlanRep.Status.PLAN_STATUS_DOING)
        factory.create_computetask(doing_cp, algo, status=ComputeTaskRep.Status.STATUS_DOING)
        self.now = doing_cp.start_date + datetime.timedelta(hours=1)

        done_cp = factory.create_computeplan(name="Done", status=ComputePlanRep.Status.PLAN_STATUS_DONE)
        factory.create_computetask(done_cp, algo, status=ComputeTaskRep.Status.STATUS_DONE)

        failed_cp = factory.create_computeplan(name="Failed", status=ComputePlanRep.Status.PLAN_STATUS_FAILED)
        failed_task = factory.create_computetask(
            failed_cp, algo, category=ComputeTaskRep.Category.TASK_TRAIN, status=ComputeTaskRep.Status.STATUS_FAILED
        )
        failed_cp.failed_task_key = str(failed_task.key)
        failed_cp.failed_task_category = failed_task.category
        failed_cp.save()

        canceled_cp = factory.create_computeplan(name="Canceled", status=ComputePlanRep.Status.PLAN_STATUS_CANCELED)
        factory.create_computetask(canceled_cp, algo, status=ComputeTaskRep.Status.STATUS_CANCELED)

        empty_cp = factory.create_computeplan(name="Empty", status=ComputePlanRep.Status.PLAN_STATUS_EMPTY)

        self.expected_results = [
            {
                "key": str(todo_cp.key),
                "tag": "",
                "name": "To do",
                "owner": "MyOrg1MSP",
                "metadata": {},
                "task_count": 1,
                "waiting_count": 0,
                "todo_count": 1,
                "doing_count": 0,
                "canceled_count": 0,
                "failed_count": 0,
                "done_count": 0,
                "failed_task": None,
                "delete_intermediary_models": False,
                "status": "PLAN_STATUS_TODO",
                "creation_date": todo_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "duration": 0,  # because start_date is None
            },
            {
                "key": str(doing_cp.key),
                "tag": "",
                "name": "Doing",
                "owner": "MyOrg1MSP",
                "metadata": {},
                "task_count": 1,
                "waiting_count": 0,
                "todo_count": 0,
                "doing_count": 1,
                "canceled_count": 0,
                "failed_count": 0,
                "done_count": 0,
                "failed_task": None,
                "delete_intermediary_models": False,
                "status": "PLAN_STATUS_DOING",
                "creation_date": doing_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": doing_cp.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": None,
                "duration": 3600,  # 1 hour (timezone.now mock with start_date + 1h)
            },
            {
                "key": str(done_cp.key),
                "tag": "",
                "name": "Done",
                "owner": "MyOrg1MSP",
                "metadata": {},
                "task_count": 1,
                "waiting_count": 0,
                "todo_count": 0,
                "doing_count": 0,
                "canceled_count": 0,
                "failed_count": 0,
                "done_count": 1,
                "failed_task": None,
                "delete_intermediary_models": False,
                "status": "PLAN_STATUS_DONE",
                "creation_date": done_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": done_cp.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": done_cp.end_date.isoformat().replace("+00:00", "Z"),
                "estimated_end_date": done_cp.end_date.isoformat().replace("+00:00", "Z"),
                "duration": 3600,  # 1 hour (default factory value)
            },
            {
                "key": str(failed_cp.key),
                "tag": "",
                "name": "Failed",
                "owner": "MyOrg1MSP",
                "metadata": {},
                "task_count": 1,
                "waiting_count": 0,
                "todo_count": 0,
                "doing_count": 0,
                "canceled_count": 0,
                "failed_count": 1,
                "done_count": 0,
                "failed_task": {
                    "key": str(failed_task.key),
                    "category": "TASK_TRAIN",
                },
                "delete_intermediary_models": False,
                "status": "PLAN_STATUS_FAILED",
                "creation_date": failed_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": failed_cp.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": failed_cp.end_date.isoformat().replace("+00:00", "Z"),
                "estimated_end_date": failed_cp.end_date.isoformat().replace("+00:00", "Z"),
                "duration": 3600,  # 1 hour (default factory value)
            },
            {
                "key": str(canceled_cp.key),
                "tag": "",
                "name": "Canceled",
                "owner": "MyOrg1MSP",
                "metadata": {},
                "task_count": 1,
                "waiting_count": 0,
                "todo_count": 0,
                "doing_count": 0,
                "canceled_count": 1,
                "failed_count": 0,
                "done_count": 0,
                "failed_task": None,
                "delete_intermediary_models": False,
                "status": "PLAN_STATUS_CANCELED",
                "creation_date": canceled_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": canceled_cp.start_date.isoformat().replace("+00:00", "Z"),
                "end_date": canceled_cp.end_date.isoformat().replace("+00:00", "Z"),
                "estimated_end_date": canceled_cp.end_date.isoformat().replace("+00:00", "Z"),
                "duration": 3600,  # 1 hour (default factory value)
            },
            {
                "key": str(empty_cp.key),
                "tag": "",
                "name": "Empty",
                "owner": "MyOrg1MSP",
                "metadata": {},
                "task_count": 0,
                "waiting_count": 0,
                "todo_count": 0,
                "doing_count": 0,
                "canceled_count": 0,
                "failed_count": 0,
                "done_count": 0,
                "failed_task": None,
                "delete_intermediary_models": False,
                "status": "PLAN_STATUS_EMPTY",
                "creation_date": empty_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "start_date": None,
                "end_date": None,
                "duration": 0,  # because start_date is None
            },
        ]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_create(self):
        key = str(uuid.uuid4())
        data = {
            "key": key,
            "tag": "foo",
            "name": "Bar",
        }

        with mock.patch.object(OrchestratorClient, "register_compute_plan", side_effect=mock_register_compute_plan):
            response = self.client.post(self.url, data=data, format="json", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data["key"])
        # asset created in local db
        self.assertEqual(ComputePlanRep.objects.count(), len(self.expected_results) + 1)

    def test_compute_plan_update(self):
        key = str(uuid.uuid4())
        data = {
            "key": key,
            "tag": "foo",
            "name": "Bar",
        }

        with mock.patch.object(OrchestratorClient, "register_compute_plan", side_effect=mock_register_compute_plan):
            response = self.client.post(self.url, data=data, format="json", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {
            "key": key,
            "name": "Foo",
        }

        url = reverse("api:compute_plan-detail", args=[key])
        compute_plan = response.data
        compute_plan["name"] = data["name"]
        with mock.patch.object(OrchestratorClient, "update_compute_plan", side_effect=compute_plan):
            response = self.client.put(url, data=data, format="json", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        error = OrcError()
        error.code = StatusCode.INTERNAL

        with mock.patch.object(OrchestratorClient, "update_compute_plan", side_effect=error):
            response = self.client.put(url, data=data, format="json", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @internal_server_error_on_exception()
    @mock.patch("api.views.computeplan.ComputePlanViewSet.create", side_effect=Exception("Unexpected error"))
    def test_computeplan_create_fail_internal_server_error(self, _):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_computeplan_list_empty(self):
        ComputePlanRep.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_computeplan_list_success(self):
        response = self.client.get(self.url, **self.extra)
        # manually overriding duration for doing cps as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for cp in response.json().get("results"):
            if cp["status"] == "PLAN_STATUS_DOING":
                cp["duration"] = 3600
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_computeplan_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("api.views.computeplan.ComputePlanViewSet.list", side_effect=Exception("Unexpected error"))
    def test_computeplan_list_fail_internal_server_error(self, _):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_computeplan_list_filter(self):
        """Filter compute_plan on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_computeplan_list_filter_and(self):
        """Filter compute_plan on key and tag."""
        key, tag = self.expected_results[0]["key"], self.expected_results[0]["tag"]
        params = urlencode({"key": key, "tag": tag})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_computeplan_list_filter_in(self):
        """Filter compute_plan in key_0, key_1"""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing cps as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for cp in response.json().get("results"):
            if cp["status"] == "PLAN_STATUS_DOING":
                cp["duration"] = 3600
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_computeplan_match(self):
        """Match compute_plan on part of the name."""
        key = self.expected_results[0]["key"]
        name = "cp156-MP-classification-PH1"
        self.expected_results[0]["name"] = name
        instance = ComputePlanRep.objects.get(key=key)
        instance.name = name
        instance.save()
        params = urlencode({"match": "cp156"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )
        params = urlencode({"match": "cp156 PH1"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_computeplan_match_and_filter(self):
        """Match compute_plan with filter."""
        key = self.expected_results[0]["key"]
        name = "cp156-MP-classification-PH1"
        self.expected_results[0]["name"] = name
        instance = ComputePlanRep.objects.get(key=key)
        instance.name = name
        instance.save()
        params = urlencode(
            {
                "key": key,
                "match": "cp156 PH1",
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    @parameterized.expand(
        [
            ("PLAN_STATUS_EMPTY"),
            ("PLAN_STATUS_WAITING"),
            ("PLAN_STATUS_TODO"),
            ("PLAN_STATUS_DOING"),
            ("PLAN_STATUS_DONE"),
            ("PLAN_STATUS_CANCELED"),
            ("PLAN_STATUS_FAILED"),
            ("PLAN_STATUS_XXX"),
        ]
    )
    def test_computeplan_list_filter_by_status(self, p_status):
        """Filter computeplan on status."""
        filtered_compute_plans = [cp for cp in self.expected_results if cp["status"] == p_status]
        params = urlencode({"status": p_status})
        response = self.client.get(f"{self.url}?{params}", **self.extra)

        if p_status != "PLAN_STATUS_XXX":
            # manually overriding duration for doing cps as "now" is taken from db and not timezone.now(),
            # couldn't be properly mocked
            if p_status == "PLAN_STATUS_DOING":
                for cp in response.json().get("results"):
                    cp["duration"] = 3600
            self.assertEqual(
                response.json(),
                {
                    "count": len(filtered_compute_plans),
                    "next": None,
                    "previous": None,
                    "results": filtered_compute_plans,
                },
            )
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            (["PLAN_STATUS_WAITING", "PLAN_STATUS_TODO"],),
            (["PLAN_STATUS_DOING", "PLAN_STATUS_XXX"],),
            (["PLAN_STATUS_DONE", "PLAN_STATUS_CANCELED", "PLAN_STATUS_FAILED"],),
        ]
    )
    def test_computeplan_list_filter_by_status_in(self, p_statuses):
        """Filter computeplan on several statuses."""
        filtered_compute_plans = [cp for cp in self.expected_results if cp["status"] in p_statuses]
        params = urlencode({"status": ",".join(p_statuses)})
        response = self.client.get(f"{self.url}?{params}", **self.extra)

        if "PLAN_STATUS_XXX" not in p_statuses:
            # manually overriding duration for doing cps as "now" is taken from db and not timezone.now(),
            # couldn't be properly mocked
            if "PLAN_STATUS_DOING" in p_statuses:
                for cp in response.json().get("results"):
                    if cp["status"] == "PLAN_STATUS_DOING":
                        cp["duration"] = 3600
            self.assertEqual(
                response.json(),
                {
                    "count": len(filtered_compute_plans),
                    "next": None,
                    "previous": None,
                    "results": filtered_compute_plans,
                },
            )
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compute_plan_list_cross_assets_filters(self):
        """Filter computeplan on other asset key such as algo_key, dataset_key and data_sample_key"""
        algo = factory.create_algo()
        data_manager = factory.create_datamanager()
        data_sample = factory.create_datasample([data_manager])

        compute_plan = factory.create_computeplan(name="cp", status=ComputePlanRep.Status.PLAN_STATUS_TODO)
        factory.create_computetask(compute_plan, algo, data_manager=data_manager, data_samples=[data_sample.key])
        expected_cp = {
            "key": str(compute_plan.key),
            "tag": "",
            "name": "cp",
            "owner": "MyOrg1MSP",
            "metadata": {},
            "task_count": 1,
            "waiting_count": 0,
            "todo_count": 1,
            "doing_count": 0,
            "canceled_count": 0,
            "failed_count": 0,
            "done_count": 0,
            "failed_task": None,
            "delete_intermediary_models": False,
            "status": "PLAN_STATUS_TODO",
            "creation_date": compute_plan.creation_date.isoformat().replace("+00:00", "Z"),
            "start_date": None,
            "end_date": None,
            "duration": 0,  # because start_date is None
        }

        # filter on algo_key
        params = urlencode({"algo_key": algo.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), [expected_cp])

        # filter on dataset_key
        params = urlencode({"dataset_key": data_manager.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), [expected_cp])

        # filter on data_sample_key
        params = urlencode({"data_sample_key": data_sample.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), [expected_cp])

    def test_computeplan_filter_by_metadata(self):
        """Match compute_plan on metadata"""
        key = self.expected_results[0]["key"]
        metadata = {
            "array": ["foo", "bar"],
            "number": 1,
            "float": 1.0,
            "string": "foo",
            'special "?= %` chars': "foo",
            "special_chars": 'special "?= %` chars',
        }
        self.expected_results[0]["metadata"] = metadata
        instance = ComputePlanRep.objects.get(key=key)
        instance.metadata = metadata
        instance.save()

        response = self.client.get(self.url, **self.extra)
        # manually overriding duration for doing cps as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for cp in response.json().get("results"):
            if cp["status"] == "PLAN_STATUS_DOING":
                cp["duration"] = 3600
        self.assertEqual(
            response.json(), {"count": 6, "next": None, "previous": None, "results": self.expected_results}
        )

        # non json data (must be ignored)
        params = urlencode({"metadata": "{not json}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing cps as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for cp in response.json().get("results"):
            if cp["status"] == "PLAN_STATUS_DOING":
                cp["duration"] = 3600
        self.assertEqual(
            response.json(), {"count": 6, "next": None, "previous": None, "results": self.expected_results}
        )

        # json data with incorrect structure (must be ignored)
        params = urlencode({"metadata": json.dumps({"dummy": "exists"})})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing cps as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for cp in response.json().get("results"):
            if cp["status"] == "PLAN_STATUS_DOING":
                cp["duration"] = 3600
        self.assertEqual(
            response.json(), {"count": 6, "next": None, "previous": None, "results": self.expected_results}
        )

        # json data with proper structure and missing keys (must be ignored)
        params = urlencode({"metadata": json.dumps([{"foo": "bar"}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        # manually overriding duration for doing cps as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for cp in response.json().get("results"):
            if cp["status"] == "PLAN_STATUS_DOING":
                cp["duration"] = 3600
        self.assertEqual(
            response.json(), {"count": 6, "next": None, "previous": None, "results": self.expected_results}
        )

        # exists
        params = urlencode({"metadata": json.dumps([{"key": "dummy", "type": "exists"}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

        params = urlencode({"metadata": json.dumps([{"key": "string", "type": "exists"}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

        # string is
        params = urlencode({"metadata": json.dumps([{"key": "string", "type": "is", "value": "foo"}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

        # string contains
        params = urlencode({"metadata": json.dumps([{"key": "string", "type": "contains", "value": "oo"}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

        # number as number (works for simple cases)
        params = urlencode({"metadata": json.dumps([{"key": "number", "type": "is", "value": 1}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

        # number as string (works)
        params = urlencode({"metadata": json.dumps([{"key": "number", "type": "is", "value": "1"}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

        # float as float (works for simple cases)
        params = urlencode({"metadata": json.dumps([{"key": "float", "type": "is", "value": 1.0}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

        # float as string (works)
        params = urlencode({"metadata": json.dumps([{"key": "float", "type": "is", "value": "1.0"}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

        # array as array (doesn't work)
        params = urlencode({"metadata": json.dumps([{"key": "array", "type": "is", "value": ["foo", "bar"]}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

        # array as string not serialized properly (doesn't work)
        params = urlencode({"metadata": json.dumps([{"key": "array", "type": "is", "value": "['foo','bar']"}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

        # array as string serialized properly (works)
        params = urlencode({"metadata": json.dumps([{"key": "array", "type": "is", "value": '["foo", "bar"]'}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

        # special chars in key (works)
        params = urlencode({"metadata": json.dumps([{"key": 'special "?= %` chars', "type": "is", "value": "foo"}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

        # special chars in value (works)
        params = urlencode(
            {"metadata": json.dumps([{"key": "special_chars", "type": "is", "value": 'special "?= %` chars'}])}
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

        # trying to be sneaky (doesn't work)
        params = urlencode({"metadata": json.dumps([{"key": "array__contains", "type": "is", "value": "foo"}])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

        # trying to be really naughty (doesn't work)
        params = urlencode(
            {
                "metadata": json.dumps(
                    [{"key": 'string); DROP TABLE "api_computeplan"; --', "type": "is", "value": "foo"}]
                )
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @parameterized.expand(
        [
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_computeplan_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        # manually overriding duration for doing cps as "now" is taken from db and not timezone.now(),
        # couldn't be properly mocked
        for cp in r["results"]:
            if cp["status"] == "PLAN_STATUS_DOING":
                cp["duration"] = 3600
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_computeplan_retrieve(self):
        url = reverse("api:compute_plan-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.expected_results[0])

    @internal_server_error_on_exception()
    @mock.patch("api.views.computeplan.ComputePlanViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_computeplan_retrieve_fail_internal_server_error(self, _):
        url = reverse("api:compute_plan-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_computeplan_cancel(self):
        url = reverse("api:compute_plan-cancel", args=[self.expected_results[0]["key"]])
        with mock.patch.object(OrchestratorClient, "cancel_compute_plan"), mock.patch.object(
            OrchestratorClient, "query_compute_plan", return_value=self.expected_results[0]
        ):
            response = self.client.post(url, **self.extra)
        self.assertEqual(response.json(), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @internal_server_error_on_exception()
    @mock.patch("api.views.computeplan.ComputePlanViewSet.cancel", side_effect=Exception("Unexpected error"))
    def test_computeplan_cancel_fail_internal_server_error(self, _):
        url = reverse("api:compute_plan-cancel", args=[self.expected_results[0]["key"]])
        response = self.client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

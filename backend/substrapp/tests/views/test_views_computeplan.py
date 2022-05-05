import datetime
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

import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
from localrep.models import ComputePlan as ComputePlanRep
from orchestrator.client import OrchestratorClient
from substrapp.tests import factory
from substrapp.views.computeplan import extract_tasks_data

from ..common import AuthenticatedClient
from ..common import internal_server_error_on_exception

MEDIA_ROOT = tempfile.mkdtemp()


def mock_register_compute_plan(data):
    """Build orchestrator register response from request data."""
    return {
        "key": data["key"],
        "tag": data["tag"],
        "metadata": data["metadata"],
        "delete_intermediary_models": data["delete_intermediary_models"],
        "status": computeplan_pb2.ComputePlanStatus.Name(computeplan_pb2.PLAN_STATUS_TODO),
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

        self.url = reverse("substrapp:compute_plan-list")

        algo = factory.create_algo()

        todo_cp = factory.create_computeplan(status=computeplan_pb2.PLAN_STATUS_TODO)
        factory.create_computetask(todo_cp, algo, status=computetask_pb2.STATUS_TODO)

        doing_cp = factory.create_computeplan(status=computeplan_pb2.PLAN_STATUS_DOING)
        factory.create_computetask(doing_cp, algo, status=computetask_pb2.STATUS_DOING)
        self.now = doing_cp.start_date + datetime.timedelta(hours=1)

        done_cp = factory.create_computeplan(status=computeplan_pb2.PLAN_STATUS_DONE)
        factory.create_computetask(done_cp, algo, status=computetask_pb2.STATUS_DONE)

        failed_cp = factory.create_computeplan(status=computeplan_pb2.PLAN_STATUS_FAILED)
        failed_task = factory.create_computetask(
            failed_cp, algo, category=computetask_pb2.TASK_TRAIN, status=computetask_pb2.STATUS_FAILED
        )
        failed_cp.failed_task_key = str(failed_task.key)
        failed_cp.failed_task_category = failed_task.category
        failed_cp.save()

        canceled_cp = factory.create_computeplan(status=computeplan_pb2.PLAN_STATUS_CANCELED)
        factory.create_computetask(canceled_cp, algo, status=computetask_pb2.STATUS_CANCELED)

        self.expected_results = [
            {
                "key": str(todo_cp.key),
                "tag": "",
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
                "duration": None,  # because start_date is None
            },
            {
                "key": str(doing_cp.key),
                "tag": "",
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
        ]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_create(self):
        dummy_key = str(uuid.uuid4())

        data = {
            "tag": "foo",
            "traintuples": [
                {
                    "algo_key": dummy_key,
                    "data_manager_key": dummy_key,
                    "train_data_sample_keys": [dummy_key],
                    "traintuple_id": dummy_key,
                }
            ],
            "testtuples": [
                {
                    "traintuple_id": dummy_key,
                    "metric_key": dummy_key,
                    "data_manager_key": dummy_key,
                }
            ],
        }

        with mock.patch.object(
            OrchestratorClient, "register_compute_plan", side_effect=mock_register_compute_plan
        ), mock.patch.object(OrchestratorClient, "register_tasks", return_value={}):
            response = self.client.post(self.url, data=data, format="json", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data["key"])
        # asset created in local db
        self.assertEqual(ComputePlanRep.objects.count(), len(self.expected_results) + 1)

    def test_create_without_tasks(self):
        data = {"tag": "foo"}

        with mock.patch.object(OrchestratorClient, "register_compute_plan", side_effect=mock_register_compute_plan):
            response = self.client.post(self.url, data=data, format="json", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data["key"])
        # asset created in local db
        self.assertEqual(ComputePlanRep.objects.count(), len(self.expected_results) + 1)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computeplan.ComputePlanViewSet.create", side_effect=Exception("Unexpected error"))
    def test_computeplan_create_fail_internal_server_error(self, _):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_computeplan_list_empty(self):
        ComputePlanRep.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_computeplan_list_success(self):
        for compute_plan in self.expected_results:
            if compute_plan["status"] == "PLAN_STATUS_UNKNOWN":
                del compute_plan["estimated_end_date"]
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_computeplan_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computeplan.ComputePlanViewSet.list", side_effect=Exception("Unexpected error"))
    def test_computeplan_list_fail_internal_server_error(self, _):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_computeplan_list_search_filter(self):
        """Filter compute_plan on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"search": f"compute_plan:key:{key}"})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_compute_plan_list_filter(self):
        """Filter compute_plan on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"key": key})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_computeplan_list_search_filter_and(self):
        """Filter compute_plan on key and tag."""
        key, tag = self.expected_results[0]["key"], self.expected_results[0]["tag"]
        params = urlencode({"search": f"compute_plan:key:{key},compute_plan:tag:{tag}"})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_compute_plan_list_filter_and(self):
        """Filter compute_plan on key and tag."""
        key, tag = self.expected_results[0]["key"], self.expected_results[0]["tag"]
        params = urlencode({"key": key, "tag": tag})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_computeplan_list_search_filter_in(self):
        """Filter compute_plan in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"search": f"compute_plan:key:{key_0},compute_plan:key:{key_1}"})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_compute_plan_list_filter_in(self):
        """Filter compute_plan in key_0, key_1"""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_computeplan_list_search_filter_or(self):
        """Filter compute_plan on key_0 or key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"search": f"compute_plan:key:{key_0}-OR-compute_plan:key:{key_1}"})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_computeplan_list_search_filter_or_and(self):
        """Filter compute_plan on (key_0 and tag_0) or (key_1 and tag_1)."""
        key_0, tag_0 = self.expected_results[0]["key"], self.expected_results[0]["tag"]
        key_1, tag_1 = self.expected_results[1]["key"], self.expected_results[1]["tag"]
        params = urlencode(
            {
                "search": (
                    f"compute_plan:key:{key_0},compute_plan:tag:{tag_0}"
                    f"-OR-compute_plan:key:{key_1},compute_plan:tag:{tag_1}"
                )
            }
        )
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_computeplan_match(self):
        """Match compute_plan on part of the tag."""
        key = self.expected_results[0]["key"]
        tag = "cp156-MP-classification-PH1"
        self.expected_results[0]["tag"] = tag
        instance = ComputePlanRep.objects.get(key=key)
        instance.tag = tag
        instance.save()
        params = urlencode({"match": "cp156"})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_computeplan_match_multiple_parts(self):
        """Match compute_plan on multiple parts of the name."""
        key = self.expected_results[0]["key"]
        tag = "cp156-MP-classification-PH1"
        self.expected_results[0]["tag"] = tag
        instance = ComputePlanRep.objects.get(key=key)
        instance.tag = tag
        instance.save()
        params = urlencode({"match": "cp156 PH1"})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_computeplan_match_and_search_filter(self):
        """Match compute_plan with filter."""
        key = self.expected_results[0]["key"]
        tag = "cp156-MP-classification-PH1"
        self.expected_results[0]["tag"] = tag
        instance = ComputePlanRep.objects.get(key=key)
        instance.tag = tag
        instance.save()
        params = urlencode(
            {
                "search": f"compute_plan:key:{key}",
                "match": "cp156 PH1",
            }
        )
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_computeplan_match_and_filter(self):
        """Match compute_plan with filter."""
        key = self.expected_results[0]["key"]
        tag = "cp156-MP-classification-PH1"
        self.expected_results[0]["tag"] = tag
        instance = ComputePlanRep.objects.get(key=key)
        instance.tag = tag
        instance.save()
        params = urlencode(
            {
                "key": key,
                "match": "cp156 PH1",
            }
        )
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    @parameterized.expand(
        [
            ("PLAN_STATUS_WAITING",),
            ("PLAN_STATUS_TODO",),
            ("PLAN_STATUS_DOING",),
            ("PLAN_STATUS_DONE",),
            ("PLAN_STATUS_CANCELED",),
            ("PLAN_STATUS_FAILED",),
            ("PLAN_STATUS_XXX",),
        ]
    )
    def test_computeplan_list_search_filter_by_status(self, p_status):
        """Filter computeplan on status."""
        filtered_compute_plans = [cp for cp in self.expected_results if cp["status"] == p_status]
        params = urlencode({"search": f"compute_plan:status:{p_status}"})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)

        if p_status != "PLAN_STATUS_XXX":
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
            ("PLAN_STATUS_WAITING",),
            ("PLAN_STATUS_TODO",),
            ("PLAN_STATUS_DOING",),
            ("PLAN_STATUS_DONE",),
            ("PLAN_STATUS_CANCELED",),
            ("PLAN_STATUS_FAILED",),
            ("PLAN_STATUS_XXX",),
        ]
    )
    def test_computeplan_list_filter_by_status(self, p_status):
        """Filter computeplan on status."""
        filtered_compute_plans = [cp for cp in self.expected_results if cp["status"] == p_status]
        params = urlencode({"status": p_status})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)

        if p_status != "PLAN_STATUS_XXX":
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
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)

        if "PLAN_STATUS_XXX" not in p_statuses:
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
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_computeplan_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        with mock.patch("localrep.serializers.computeplan.timezone.now", return_value=self.now):
            response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_computeplan_retrieve(self):
        url = reverse("substrapp:compute_plan-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.expected_results[0])

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computeplan.ComputePlanViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_computeplan_retrieve_fail_internal_server_error(self, _):
        url = reverse("substrapp:compute_plan-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_computeplan_cancel(self):
        url = reverse("substrapp:compute_plan-cancel", args=[self.expected_results[0]["key"]])
        with mock.patch.object(OrchestratorClient, "cancel_compute_plan"), mock.patch.object(
            OrchestratorClient, "query_compute_plan", return_value=self.expected_results[0]
        ):
            response = self.client.post(url, **self.extra)
        self.assertEqual(response.json(), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.computeplan.ComputePlanViewSet.cancel", side_effect=Exception("Unexpected error"))
    def test_computeplan_cancel_fail_internal_server_error(self, _):
        url = reverse("substrapp:compute_plan-cancel", args=[self.expected_results[0]["key"]])
        response = self.client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_extract_tasks_data(self):
        dummy_key = str(uuid.uuid4())
        dummy_key2 = str(uuid.uuid4())

        composite = {
            "composite_traintuples": [
                {
                    "composite_traintuple_id": dummy_key,
                    "in_head_model_id": dummy_key,
                    "in_trunk_model_id": dummy_key2,
                    "algo_key": dummy_key,
                    "metadata": {"simple_metadata": "data"},
                    "data_manager_key": dummy_key,
                    "train_data_sample_keys": [dummy_key, dummy_key],
                    "out_trunk_model_permissions": {"public": False, "authorized_ids": ["test-org"]},
                }
            ]
        }

        tasks = extract_tasks_data(composite, dummy_key)
        self.assertEqual(len(tasks[0]["parent_task_keys"]), 2)

    @internal_server_error_on_exception()
    @mock.patch(
        "substrapp.views.computeplan.ComputePlanViewSet.update_ledger", side_effect=Exception("Unexpected error")
    )
    def test_computeplan_update_ledger_fail_internal_server_error(self, _):
        url = reverse("substrapp:compute_plan-update-ledger", kwargs={"pk": self.expected_results[0]["key"]})
        response = self.client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

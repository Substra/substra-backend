import os
import shutil
import tempfile
from uuid import uuid4

from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework.test import APITestCase

from api.models import ComputePlan
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT, CHANNELS={"mychannel": {"model_export_enabled": True}})
class NewsFeedViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.url = reverse("api:news_feed-list")

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_newsfeed_list_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_newsfeed_list(self):
        # first all CPs are created in the order below
        # then they all start in the same order (depending on the status)
        # finally they all end in the same order (depending on the status)
        created_cp = factory.create_computeplan(
            status=ComputePlan.Status.PLAN_STATUS_CREATED
        )  # no start_date, end_date
        doing_cp = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DOING)  # no end_date
        canceled_cp = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_CANCELED)
        failed_cp = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_FAILED)
        failed_cp.failed_task_key = str(uuid4())
        failed_cp.save()
        done_cp = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DONE)
        datamanager = factory.create_datamanager()

        # we expect items to be sorted from the latest to the earliest
        expected_results = [
            # PLAN_STATUS_DONE
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(done_cp.key),
                "name": str(done_cp.name),
                "status": "STATUS_DONE",
                "timestamp": done_cp.end_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            # PLAN_STATUS_FAILED
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(failed_cp.key),
                "name": str(failed_cp.name),
                "status": "STATUS_FAILED",
                "timestamp": failed_cp.end_date.isoformat().replace("+00:00", "Z"),
                "detail": {
                    "first_failed_task_key": failed_cp.failed_task_key,
                },
            },
            # PLAN_STATUS_CANCELED
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(canceled_cp.key),
                "name": str(canceled_cp.name),
                "status": "STATUS_CANCELED",
                "timestamp": canceled_cp.end_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            # PLAN_STATUS_DOING
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(done_cp.key),
                "name": str(done_cp.name),
                "status": "STATUS_DOING",
                "timestamp": done_cp.start_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(failed_cp.key),
                "name": str(failed_cp.name),
                "status": "STATUS_DOING",
                "timestamp": failed_cp.start_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(canceled_cp.key),
                "name": str(canceled_cp.name),
                "status": "STATUS_DOING",
                "timestamp": canceled_cp.start_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(doing_cp.key),
                "name": str(doing_cp.name),
                "status": "STATUS_DOING",
                "timestamp": doing_cp.start_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            # DATAMANAGER
            {
                "asset_kind": "ASSET_DATA_MANAGER",
                "asset_key": str(datamanager.key),
                "name": str(datamanager.name),
                "status": "STATUS_CREATED",
                "timestamp": datamanager.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            # PLAN_STATUS_CREATED
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(done_cp.key),
                "name": str(done_cp.name),
                "status": "STATUS_CREATED",
                "timestamp": done_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(failed_cp.key),
                "name": str(failed_cp.name),
                "status": "STATUS_CREATED",
                "timestamp": failed_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(canceled_cp.key),
                "name": str(canceled_cp.name),
                "status": "STATUS_CREATED",
                "timestamp": canceled_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(doing_cp.key),
                "name": str(doing_cp.name),
                "status": "STATUS_CREATED",
                "timestamp": doing_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(created_cp.key),
                "name": str(created_cp.name),
                "status": "STATUS_CREATED",
                "timestamp": created_cp.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
        ]

        response = self.client.get(self.url)
        self.assertEqual(
            response.json(),
            {"count": len(expected_results), "next": None, "previous": None, "results": expected_results},
        )

    def test_newsfeed_filter_creation_date(self):
        cp = factory.create_computeplan()
        datamanager1 = factory.create_datamanager()
        datamanager2 = factory.create_datamanager()

        expected_results = [
            {
                "asset_kind": "ASSET_DATA_MANAGER",
                "asset_key": str(datamanager2.key),
                "name": str(datamanager2.name),
                "status": "STATUS_CREATED",
                "timestamp": datamanager2.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_DATA_MANAGER",
                "asset_key": str(datamanager1.key),
                "name": str(datamanager1.name),
                "status": "STATUS_CREATED",
                "timestamp": datamanager1.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(cp.key),
                "name": str(cp.name),
                "status": "STATUS_CREATED",
                "timestamp": cp.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
        ]

        response = self.client.get(self.url)
        self.assertEqual(
            response.json(),
            {"count": len(expected_results), "next": None, "previous": None, "results": expected_results},
        )

        params = urlencode({"timestamp_after": expected_results[2]["timestamp"]})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(),
            {"count": 3, "next": None, "previous": None, "results": expected_results[:3]},
        )

        params = urlencode({"timestamp_before": expected_results[0]["timestamp"]})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(),
            {"count": 2, "next": None, "previous": None, "results": expected_results[1:]},
        )

        params = urlencode(
            {"timestamp_before": expected_results[1]["timestamp"], "timestamp_after": expected_results[2]["timestamp"]}
        )
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(),
            {"count": 1, "next": None, "previous": None, "results": [expected_results[2]]},
        )

    def test_newsfeed_filter_start_end_date(self):
        cp = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DONE)

        expected_results = [
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(cp.key),
                "name": str(cp.name),
                "status": "STATUS_DONE",
                "timestamp": cp.end_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(cp.key),
                "name": str(cp.name),
                "status": "STATUS_DOING",
                "timestamp": cp.start_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(cp.key),
                "name": str(cp.name),
                "status": "STATUS_CREATED",
                "timestamp": cp.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
        ]

        response = self.client.get(self.url)
        self.assertEqual(
            response.json(),
            {"count": len(expected_results), "next": None, "previous": None, "results": expected_results},
        )

        params = urlencode({"timestamp_after": expected_results[1]["timestamp"]})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(),
            {"count": 2, "next": None, "previous": None, "results": expected_results[:2]},
        )

        params = urlencode({"timestamp_before": expected_results[0]["timestamp"]})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(),
            {"count": 2, "next": None, "previous": None, "results": expected_results[1:]},
        )

        params = urlencode(
            {"timestamp_before": expected_results[0]["timestamp"], "timestamp_after": expected_results[1]["timestamp"]}
        )
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(),
            {"count": 1, "next": None, "previous": None, "results": [expected_results[1]]},
        )

    def test_newsfeed_filter_important_news_only(self):
        cp = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DONE)
        datamanager = factory.create_datamanager()

        expected_results = [
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(cp.key),
                "name": str(cp.name),
                "status": "STATUS_DONE",
                "timestamp": cp.end_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(cp.key),
                "name": str(cp.name),
                "status": "STATUS_DOING",
                "timestamp": cp.start_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_DATA_MANAGER",
                "asset_key": str(datamanager.key),
                "name": str(datamanager.name),
                "status": "STATUS_CREATED",
                "timestamp": datamanager.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": str(cp.key),
                "name": str(cp.name),
                "status": "STATUS_CREATED",
                "timestamp": cp.creation_date.isoformat().replace("+00:00", "Z"),
                "detail": {},
            },
        ]

        response = self.client.get(self.url)
        self.assertEqual(
            response.json(),
            {"count": len(expected_results), "next": None, "previous": None, "results": expected_results},
        )

        params = urlencode({"important_news_only": "true"})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(),
            {"count": 1, "next": None, "previous": None, "results": [expected_results[0]]},
        )

        params = urlencode({"important_news_only": "false"})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(),
            {"count": len(expected_results), "next": None, "previous": None, "results": expected_results},
        )

        params = urlencode({"important_news_only": "else"})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(),
            {"count": len(expected_results), "next": None, "previous": None, "results": expected_results},
        )

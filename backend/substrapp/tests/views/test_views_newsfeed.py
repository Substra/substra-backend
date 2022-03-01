import os
import shutil
import tempfile
from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

import orchestrator.computeplan_pb2 as computeplan_pb2
from localrep.models import ComputePlan as ComputePlanRep

from ..common import AuthenticatedClient

MEDIA_ROOT = tempfile.mkdtemp()


def add_cp_with_dates(status):
    """
    Add computeplan with:
        - creation_date now
        - start_date in 1h (depending on the status)
        - end_date in 2h (depending on the status)
    """
    compute_plan = ComputePlanRep(
        key=uuid4(),
        status=status,
        creation_date=datetime.now(),
        tag="",
        owner="MyOrg1MSP",
        channel="mychannel",
    )
    if status in (
        computeplan_pb2.PLAN_STATUS_DOING,
        computeplan_pb2.PLAN_STATUS_DONE,
        computeplan_pb2.PLAN_STATUS_FAILED,
        computeplan_pb2.PLAN_STATUS_CANCELED,
    ):
        compute_plan.start_date = compute_plan.creation_date + timedelta(hours=1)
    if status in (
        computeplan_pb2.PLAN_STATUS_DONE,
        computeplan_pb2.PLAN_STATUS_FAILED,
        computeplan_pb2.PLAN_STATUS_CANCELED,
    ):
        compute_plan.end_date = compute_plan.creation_date + timedelta(hours=2)
    if status == computeplan_pb2.PLAN_STATUS_FAILED:
        compute_plan.failed_task_key = str(uuid4())
        compute_plan.failed_task_category = 0
    compute_plan.save()
    return compute_plan


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
)
class NewsFeedViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        self.url = reverse("substrapp:news_feed-list")

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_newsfeed_list_empty(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_newsfeed_list(self):
        # first all CPs are created in the order below
        # then they all start in the same order (depending on the status)
        # finally they all end in the same order (depending on the status)
        todo_cp = add_cp_with_dates(computeplan_pb2.PLAN_STATUS_TODO)  # no start_date, end_date
        doing_cp = add_cp_with_dates(computeplan_pb2.PLAN_STATUS_DOING)  # no end_date
        canceled_cp = add_cp_with_dates(computeplan_pb2.PLAN_STATUS_CANCELED)
        failed_cp = add_cp_with_dates(computeplan_pb2.PLAN_STATUS_FAILED)
        done_cp = add_cp_with_dates(computeplan_pb2.PLAN_STATUS_DONE)

        # we expect items to be sorted from the latest to the earliest
        expected_items = [
            # PLAN_STATUS_DONE
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": done_cp.key,
                "status": "STATUS_DONE",
                "timestamp": done_cp.end_date,
                "detail": {},
            },
            # PLAN_STATUS_FAILED
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": failed_cp.key,
                "status": "STATUS_FAILED",
                "timestamp": failed_cp.end_date,
                "detail": {
                    "first_failed_task_key": failed_cp.failed_task_key,
                    "task_category": failed_cp.failed_task_category,
                },
            },
            # PLAN_STATUS_CANCELED
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": canceled_cp.key,
                "status": "STATUS_CANCELED",
                "timestamp": canceled_cp.end_date,
                "detail": {},
            },
            # PLAN_STATUS_DOING
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": done_cp.key,
                "status": "STATUS_DOING",
                "timestamp": done_cp.start_date,
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": failed_cp.key,
                "status": "STATUS_DOING",
                "timestamp": failed_cp.start_date,
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": canceled_cp.key,
                "status": "STATUS_DOING",
                "timestamp": canceled_cp.start_date,
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": doing_cp.key,
                "status": "STATUS_DOING",
                "timestamp": doing_cp.start_date,
                "detail": {},
            },
            # PLAN_STATUS_CREATED
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": done_cp.key,
                "status": "STATUS_CREATED",
                "timestamp": done_cp.creation_date,
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": failed_cp.key,
                "status": "STATUS_CREATED",
                "timestamp": failed_cp.creation_date,
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": canceled_cp.key,
                "status": "STATUS_CREATED",
                "timestamp": canceled_cp.creation_date,
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": doing_cp.key,
                "status": "STATUS_CREATED",
                "timestamp": doing_cp.creation_date,
                "detail": {},
            },
            {
                "asset_kind": "ASSET_COMPUTE_PLAN",
                "asset_key": todo_cp.key,
                "status": "STATUS_CREATED",
                "timestamp": todo_cp.creation_date,
                "detail": {},
            },
        ]
        for item in expected_items:
            item["asset_key"] = str(item["asset_key"])
            item["timestamp"] = item["timestamp"].isoformat() + "Z"

        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(expected_items), "next": None, "previous": None, "results": expected_items},
        )

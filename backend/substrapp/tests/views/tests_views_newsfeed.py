import copy
import os
import shutil
import uuid

import mock
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orchestrator.client import OrchestratorClient

from .. import assets
from ..common import AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


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

    first_failed_task_key = str(uuid.uuid4())
    compute_plan_key = "bbd623b2-9615-48c1-9370-3fca9dd2c0f2"
    compute_plan_key_2 = str(uuid.uuid4())

    compute_plan_events = [
        {
            "id": "ba36c764-1764-4732-894f-a98427bd039a",
            "asset_key": compute_plan_key,
            "asset_kind": "ASSET_COMPUTE_PLAN",
            "event_kind": "EVENT_ASSET_CREATED",
            "channel": "mychannel",
            "timestamp": "2021-12-09T14:10:00.121196200Z",
            "metadata": {"creator": "MyOrg1MSP"},
        }
    ]

    compute_task_events = [
        {
            "id": "random_id",
            "asset_key": "random_key",
            "asset_kind": "ASSET_COMPUTE_TASK",
            "event_kind": "EVENT_ASSET_UPDATED",
            "channel": "mychannel",
            "timestamp": "2021-12-09T14:05:00.121196200Z",
            "metadata": {
                "worker": "MyOrg1MSP",
                "status": "STATUS_TODO",
                "compute_plan_key": compute_plan_key,
                "reason": "User action",
            },
        },
        {
            "id": "random_id",
            "asset_key": "random_key",
            "asset_kind": "ASSET_COMPUTE_TASK",
            "event_kind": "EVENT_ASSET_UPDATED",
            "channel": "mychannel",
            "timestamp": "2021-12-09T14:20:00.121196200Z",
            "metadata": {
                "worker": "MyOrg1MSP",
                "status": "STATUS_DOING",
                "compute_plan_key": compute_plan_key,
                "reason": "User action",
            },
        },
        {
            "id": "random_id",
            "asset_key": first_failed_task_key,
            "asset_kind": "ASSET_COMPUTE_TASK",
            "event_kind": "EVENT_ASSET_UPDATED",
            "channel": "mychannel",
            "timestamp": "2021-12-09T14:30:00.121196200Z",
            "metadata": {
                "worker": "MyOrg1MSP",
                "compute_plan_key": compute_plan_key,
                "status": "STATUS_FAILED",
                "reason": "[00-01-0000-3f521d6]",
            },
        },
        {
            "id": "random_id",
            "asset_key": "random key",
            "asset_kind": "ASSET_COMPUTE_TASK",
            "event_kind": "EVENT_ASSET_UPDATED",
            "channel": "mychannel",
            "timestamp": "2021-12-09T14:40:00.121196200Z",
            "metadata": {
                "worker": "MyOrg1MSP",
                "compute_plan_key": compute_plan_key,
                "status": "STATUS_FAILED",
                "reason": "[00-01-0000-3f521d6]",
            },
        },
        {
            "id": "random_id",
            "asset_key": "random_key",
            "asset_kind": "ASSET_COMPUTE_TASK",
            "event_kind": "EVENT_ASSET_UPDATED",
            "channel": "mychannel",
            "timestamp": "2021-12-09T14:50:00.121196200Z",
            "metadata": {
                "worker": "MyOrg1MSP",
                "reason": "All performances registered on bf413710-90fa-4d2f-8b58-657e9918b9f7 by MyOrg1MSP",
                "compute_plan_key": compute_plan_key_2,
                "status": "STATUS_DONE",
            },
        },
    ]

    def test_can_see_news_feed(self):
        cp = assets.get_compute_plan()
        cp_response = copy.deepcopy(cp)

        url = reverse("substrapp:news_feed-list")

        with mock.patch.object(OrchestratorClient, "query_compute_plan", return_value=cp_response), mock.patch.object(
            OrchestratorClient, "query_events", side_effect=[self.compute_plan_events, self.compute_task_events]
        ):
            response = self.client.get(url, **self.extra)
            actual = response.json()

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Only one news per compute plan status
            self.assertEqual(len(actual["results"]), 4)

            self.assertEqual(actual["results"][0]["asset_kind"], "ASSET_COMPUTE_PLAN")
            self.assertEqual(actual["results"][0]["asset_key"], self.compute_plan_key_2)
            self.assertEqual(actual["results"][0]["status"], "STATUS_DONE")

            self.assertEqual(actual["results"][1]["asset_kind"], "ASSET_COMPUTE_PLAN")
            self.assertEqual(actual["results"][1]["asset_key"], self.compute_plan_key)
            self.assertEqual(actual["results"][1]["status"], "STATUS_FAILED")

            self.assertEqual(actual["results"][2]["asset_kind"], "ASSET_COMPUTE_PLAN")
            self.assertEqual(actual["results"][2]["asset_key"], self.compute_plan_key)
            self.assertEqual(actual["results"][2]["status"], "STATUS_DOING")

            self.assertEqual(actual["results"][3]["asset_kind"], "ASSET_COMPUTE_PLAN")
            self.assertEqual(actual["results"][3]["asset_key"], self.compute_plan_key)
            self.assertEqual(actual["results"][3]["status"], "STATUS_CREATED")

            # test can see lattest failed compute task
            for event in actual["results"]:
                if event["status"] == "STATUS_FAILED":
                    self.assertEqual(event["detail"]["first_failed_task_key"], self.first_failed_task_key)

            # test can see failed compute task detail
            for event in actual["results"]:
                if event["status"] == "STATUS_FAILED":
                    self.assertTrue(len(event["detail"]), "news item has no detail")
                elif event["status"] in ("STATUS_CREATED", "STATUS_DOING", "STATUS_DONE"):
                    self.assertFalse(len(event["detail"]), "news item should not have detail")

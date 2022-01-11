import uuid
from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.test import override_settings

import events.localsync as localsync
import orchestrator.common_pb2 as common_pb2
import orchestrator.event_pb2 as event_pb2
from localrep.models.event import Event
from orchestrator.client import OrchestratorClient


@override_settings(LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}}})
class LocalSyncTests(TestCase):
    """Localsync tests"""

    def setUp(self):
        self.orchestrator_events = [
            {
                "timestamp": "2000-01-01T01:00:00.0000",
            },
            {
                "timestamp": "2000-01-02T01:00:00.0000",
            },
            {
                "timestamp": "2000-01-02T01:00:00.0000",
            },
            {
                "timestamp": "2000-01-03T01:00:00.0000",
            },
        ]
        self.channel = "mychannel"

    def test_resync(self):
        # test first sync no local events
        with mock.patch.object(
            OrchestratorClient, "query_events_generator", return_value=iter(self.orchestrator_events)
        ), mock.patch("events.localsync.sync_on_event_message") as msync:
            localsync.resync()
            self.assertEqual(msync.call_count, 4)

        # test partial resync
        Event.objects.create(
            id=uuid.uuid4(),
            asset_key=uuid.uuid4(),
            asset_kind=common_pb2.ASSET_NODE,
            event_kind=event_pb2.EVENT_ASSET_CREATED,
            channel=self.channel,
            timestamp=datetime(2000, 1, 1, tzinfo="US/Eastern"),
        )

        with mock.patch.object(
            OrchestratorClient, "query_events_generator", return_value=iter(self.orchestrator_events)
        ), mock.patch("events.localsync.sync_on_event_message") as msync:
            localsync.resync()
            self.assertEqual(msync.call_count, 3)

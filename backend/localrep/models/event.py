from django.db import models

import orchestrator.common_pb2 as common_pb2
import orchestrator.event_pb2 as event_pb2
from localrep.models.utils import get_enum_choices


class Event(models.Model):
    """Events are created by the orchestrator at each asset updates (creation and status updates).
    They are used by: 1. The Front End client to display the news feed
                      2. The backend Event App to resync the local representation from the last local event
    """

    ASSET_KIND = get_enum_choices(common_pb2.AssetKind)
    EVENT_KIND = get_enum_choices(event_pb2.EventKind)

    id = models.UUIDField(primary_key=True)
    asset_key = models.CharField(max_length=100)
    asset_kind = models.IntegerField(choices=ASSET_KIND)
    event_kind = models.IntegerField(choices=EVENT_KIND)
    channel = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    metadata = models.JSONField(null=True)

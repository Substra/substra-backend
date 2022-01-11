import structlog
from rest_framework import serializers

import orchestrator.common_pb2 as common_pb2
import orchestrator.event_pb2 as event_pb2
from localrep.models import Event
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices

logger = structlog.get_logger(__name__)


class AssetKindField(serializers.Field):
    def to_representation(self, value):
        return common_pb2.AssetKind.Name(value)

    def to_internal_value(self, value):
        return common_pb2.AssetKind.Value(value)


class EventKindField(serializers.Field):
    def to_representation(self, value):
        return event_pb2.EventKind.Name(value)

    def to_internal_value(self, value):
        return event_pb2.EventKind.Value(value)


class EventSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    asset_kind = AssetKindField()
    event_kind = EventKindField()
    channel = serializers.ChoiceField(choices=get_channel_choices())

    primary_key_name = "id"

    class Meta:
        model = Event
        fields = [
            "id",
            "asset_key",
            "asset_kind",
            "event_kind",
            "channel",
            "timestamp",
            "metadata",
        ]

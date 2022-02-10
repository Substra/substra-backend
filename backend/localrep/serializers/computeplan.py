from rest_framework import serializers

from localrep.models import ComputePlan
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from orchestrator import computeplan_pb2


class ComputePlanSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    task_count = serializers.IntegerField(read_only=True)
    done_count = serializers.IntegerField(read_only=True)
    waiting_count = serializers.IntegerField(read_only=True)
    todo_count = serializers.IntegerField(read_only=True)
    doing_count = serializers.IntegerField(read_only=True)
    canceled_count = serializers.IntegerField(read_only=True)
    failed_count = serializers.IntegerField(read_only=True)
    status = serializers.ChoiceField(read_only=True, choices=computeplan_pb2.ComputePlanStatus.keys())

    class Meta:
        model = ComputePlan
        fields = [
            "key",
            "owner",
            "delete_intermediary_models",
            "tag",
            "creation_date",
            "metadata",
            "channel",
            "task_count",
            "done_count",
            "waiting_count",
            "todo_count",
            "doing_count",
            "canceled_count",
            "failed_count",
            "status",
        ]

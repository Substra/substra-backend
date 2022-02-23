from rest_framework import serializers

from localrep.models import ComputePlan
from localrep.serializers.computetask import CategoryField
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from orchestrator import computeplan_pb2


class FailedTaskSerializer(serializers.Serializer):
    key = serializers.CharField(required=False, allow_null=True, max_length=64, source="failed_task_key")
    category = CategoryField(
        required=False,
        allow_null=True,
        source="failed_task_category",
    )


class StatusField(serializers.Field):
    def to_representation(self, instance):
        return computeplan_pb2.ComputePlanStatus.Name(instance)

    def to_internal_value(self, data):
        return computeplan_pb2.ComputePlanStatus.Value(data)


class ComputePlanSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    task_count = serializers.IntegerField(read_only=True)
    done_count = serializers.IntegerField(read_only=True)
    waiting_count = serializers.IntegerField(read_only=True)
    todo_count = serializers.IntegerField(read_only=True)
    doing_count = serializers.IntegerField(read_only=True)
    canceled_count = serializers.IntegerField(read_only=True)
    failed_count = serializers.IntegerField(read_only=True)
    status = StatusField()
    failed_task = FailedTaskSerializer(read_only=True, allow_null=True, required=False, source="*")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.failed_task_key:
            # None should be returned to the API not the default OrderedDict
            data["failed_task"] = None
        return data

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
            "failed_task",
            "task_count",
            "done_count",
            "waiting_count",
            "todo_count",
            "doing_count",
            "canceled_count",
            "failed_count",
            "status",
        ]

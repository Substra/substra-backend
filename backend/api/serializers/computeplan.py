import datetime

from django.utils import timezone
from rest_framework import serializers

from api.models import ComputePlan
from api.models.computetask import ComputeTask
from api.serializers.utils import SafeSerializerMixin
from api.serializers.utils import get_channel_choices


class FailedTaskSerializer(serializers.Serializer):
    key = serializers.CharField(required=False, allow_null=True, max_length=64, source="failed_task_key")
    category = serializers.ChoiceField(
        choices=ComputeTask.Category.choices,
        required=False,
        allow_null=True,
        source="failed_task_category",
    )


class ComputePlanSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    failed_task = FailedTaskSerializer(read_only=True, allow_null=True, required=False, source="*")
    duration = serializers.IntegerField(read_only=True)
    status = serializers.ChoiceField(choices=ComputePlan.Status.choices, read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if not instance.failed_task_key:
            # None should be returned to the API not the default OrderedDict
            data["failed_task"] = None

        data.update(instance.get_task_stats())
        data = self._add_compute_plan_estimated_end_date(data)

        return data

    def _add_compute_plan_estimated_end_date(self, data):
        """Add the estimated time of arrival to a compute plan data."""

        if data["status"] == ComputePlan.Status.PLAN_STATUS_DOING:
            if data["done_count"] and data["start_date"] is not None:
                remaining_tasks_count = data["task_count"] - data["done_count"]
                time_per_task = data["duration"] / data["done_count"]
                estimated_duration = remaining_tasks_count * time_per_task
                data["estimated_end_date"] = (timezone.now() + datetime.timedelta(seconds=estimated_duration)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                )
        elif data["status"] in [
            ComputePlan.Status.PLAN_STATUS_FAILED,
            ComputePlan.Status.PLAN_STATUS_CANCELED,
            ComputePlan.Status.PLAN_STATUS_DONE,
        ]:
            data["estimated_end_date"] = data["end_date"]
        return data

    class Meta:
        model = ComputePlan
        fields = [
            "key",
            "owner",
            "delete_intermediary_models",
            "tag",
            "name",
            "creation_date",
            "start_date",
            "end_date",
            "duration",
            "metadata",
            "channel",
            "failed_task",
            "status",
        ]

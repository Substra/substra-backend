import datetime

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from api.models import ComputePlan
from api.serializers.utils import SafeSerializerMixin
from api.serializers.utils import get_channel_choices


class ComputePlanSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    duration = serializers.IntegerField(read_only=True)
    status = serializers.ChoiceField(choices=ComputePlan.Status.choices, read_only=True)
    creator = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def to_representation(self, instance):
        data = super().to_representation(instance)
        creator = data["creator"]
        if creator:
            data["creator"] = User.objects.get(id=creator).username

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
            "tag",
            "name",
            "creator",
            "creation_date",
            "start_date",
            "end_date",
            "duration",
            "metadata",
            "channel",
            "failed_task_key",
            "status",
        ]

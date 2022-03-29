import datetime

from django.db.models import Count
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from localrep.models import ComputePlan
from localrep.models.computetask import ComputeTask
from localrep.serializers.computetask import CategoryField
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from orchestrator import computeplan_pb2
from orchestrator import computetask_pb2


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
    duration = serializers.SerializerMethodField()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if not instance.failed_task_key:
            # None should be returned to the API not the default OrderedDict
            data["failed_task"] = None

        data = self._add_cp_task_counts(data)
        data = self._add_compute_plan_estimated_end_date(data)

        return data

    def _add_cp_task_counts(self, data):
        stats = ComputeTask.objects.filter(compute_plan__key=data["key"]).aggregate(
            task_count=Count("key"),
            done_count=Count("key", filter=Q(status=computetask_pb2.STATUS_DONE)),
            waiting_count=Count("key", filter=Q(status=computetask_pb2.STATUS_WAITING)),
            todo_count=Count("key", filter=Q(status=computetask_pb2.STATUS_TODO)),
            doing_count=Count("key", filter=Q(status=computetask_pb2.STATUS_DOING)),
            canceled_count=Count("key", filter=Q(status=computetask_pb2.STATUS_CANCELED)),
            failed_count=Count("key", filter=Q(status=computetask_pb2.STATUS_FAILED)),
        )
        data.update(stats)
        return data

    def _add_compute_plan_estimated_end_date(self, data):
        """Add the estimated time of arrival to a compute plan data."""

        compute_plan_status = computeplan_pb2.ComputePlanStatus.Value(data["status"])

        if compute_plan_status == computeplan_pb2.PLAN_STATUS_DOING:
            if data["done_count"] and data["start_date"] is not None:
                remaining_tasks_count = data["task_count"] - data["done_count"]
                time_per_task = data["duration"] / data["done_count"]
                estimated_duration = remaining_tasks_count * time_per_task
                data["estimated_end_date"] = (timezone.now() + datetime.timedelta(seconds=estimated_duration)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                )
        elif compute_plan_status in [
            computeplan_pb2.PLAN_STATUS_FAILED,
            computeplan_pb2.PLAN_STATUS_CANCELED,
            computeplan_pb2.PLAN_STATUS_DONE,
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
            "creation_date",
            "start_date",
            "end_date",
            "duration",
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

    def get_duration(self, instance):
        if not instance.start_date:
            return None
        return ((instance.end_date or timezone.now()) - instance.start_date).seconds

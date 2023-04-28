from rest_framework import serializers

from api.models import ComputeTask
from api.models import ComputeTaskOutput
from api.models import Function
from api.models import Performance
from api.serializers.utils import SafeSerializerMixin


class PerformanceSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    # overwrite primary key field for the SafeSerializerMixin check
    # the unique constraint for compute_task_key + metric_key in the model
    # ensures no duplicates are created
    primary_key_name = "id"

    compute_task_output_key = serializers.PrimaryKeyRelatedField(
        queryset=ComputeTaskOutput.objects.all(),
        source="compute_task_output",
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )

    metric_key = serializers.PrimaryKeyRelatedField(
        queryset=Function.objects.all(), source="metric", pk_field=serializers.UUIDField(format="hex_verbose")
    )
    performance_value = serializers.FloatField(source="value")

    class Meta:
        model = Performance
        fields = [
            "channel",
            "compute_task_output_key",
            "creation_date",
            "metric_key",
            "performance_value",
        ]


class _PerformanceMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Function
        fields = ["key", "name"]


class _PerformanceComputeTaskSerializer(serializers.ModelSerializer):
    function_key = serializers.UUIDField(format="hex_verbose", source="function_id")
    round_idx = serializers.SerializerMethodField()

    class Meta:
        model = ComputeTask
        fields = [
            "key",
            "function_key",
            "rank",
            "round_idx",
            "worker",
        ]

    def get_round_idx(self, instance):
        return instance.metadata.get("round_idx")


class CPPerformanceSerializer(serializers.ModelSerializer):
    compute_task = _PerformanceComputeTaskSerializer(read_only=True, source="compute_task_output.task")
    metric = _PerformanceMetricSerializer(read_only=True)
    identifier = serializers.CharField(source="compute_task_output.identifier")
    perf = serializers.FloatField(source="value")

    class Meta:
        model = Performance
        fields = [
            "compute_task",
            "metric",
            "identifier",
            "perf",
        ]


class ExportPerformanceSerializer(serializers.ModelSerializer):
    compute_plan_key = serializers.UUIDField()
    compute_plan_name = serializers.CharField()
    compute_plan_tag = serializers.CharField()
    compute_plan_status = serializers.CharField()
    compute_plan_start_date = serializers.DateTimeField()
    compute_plan_end_date = serializers.DateTimeField()
    compute_plan_metadata = serializers.JSONField()
    function_name = serializers.CharField()
    worker = serializers.CharField()
    task_rank = serializers.IntegerField()
    task_round = serializers.IntegerField()
    performance = serializers.FloatField()

    class Meta:
        model = Performance
        fields = [
            "compute_plan_key",
            "compute_plan_name",
            "compute_plan_tag",
            "compute_plan_status",
            "compute_plan_start_date",
            "compute_plan_end_date",
            "compute_plan_metadata",
            "function_name",
            "worker",
            "task_rank",
            "task_round",
            "performance",
        ]

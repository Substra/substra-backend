from rest_framework import serializers

from api.models import ComputeTask
from api.models import ComputeTaskOutput
from api.models import Performance
from api.serializers.utils import SafeSerializerMixin


class PerformanceSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    # overwrite primary key field for the SafeSerializerMixin check
    # the unique constraint for compute_task_output + metric in the model
    # ensures no duplicates are created
    primary_key_name = "id"

    # necessary to get the ComputeTaskOutput to create the Performance
    compute_task_key = serializers.UUIDField(format="hex_verbose", source="compute_task_output.task_id")
    compute_task_output_identifier = serializers.CharField(source="compute_task_output.identifier")

    performance_value = serializers.FloatField(source="value")

    class Meta:
        model = Performance
        fields = [
            "channel",
            "compute_task_key",
            "creation_date",
            "compute_task_output_identifier",
            "performance_value",
        ]

    def create(self, validated_data):
        task_output = ComputeTaskOutput.objects.get(
            task__key=validated_data["compute_task_output"]["task_id"],
            identifier=validated_data["compute_task_output"]["identifier"],
            channel=validated_data["channel"],
        )

        performance = Performance(
            compute_task_output=task_output,
            channel=validated_data["channel"],
            creation_date=validated_data["creation_date"],
            value=validated_data["value"],
        )
        performance.save()
        return performance


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
    identifier = serializers.CharField(source="compute_task_output.identifier")
    perf = serializers.FloatField(source="value")

    class Meta:
        model = Performance
        fields = [
            "compute_task",
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
    worker = serializers.CharField()
    task_rank = serializers.IntegerField()
    task_round = serializers.IntegerField()
    identifier = serializers.CharField()
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
            "worker",
            "task_rank",
            "task_round",
            "identifier",
            "performance",
        ]

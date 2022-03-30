from rest_framework import serializers

from localrep.models import ComputeTask
from localrep.models import Metric
from localrep.models import Performance
from localrep.serializers.utils import SafeSerializerMixin


class PerformanceSerializer(serializers.ModelSerializer, SafeSerializerMixin):

    # overwrite primary key field for the SafeSerializerMixin check
    # the unique constraint for compute_task_key + metric_key in the model
    # ensures no duplicates are created
    primary_key_name = "id"

    compute_task_key = serializers.PrimaryKeyRelatedField(
        queryset=ComputeTask.objects.all(), source="compute_task", pk_field=serializers.UUIDField(format="hex_verbose")
    )

    metric_key = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all(), source="metric", pk_field=serializers.UUIDField(format="hex_verbose")
    )
    performance_value = serializers.FloatField(source="value")

    class Meta:
        model = Performance
        fields = [
            "channel",
            "compute_task_key",
            "creation_date",
            "metric_key",
            "performance_value",
        ]


class _PerformanceMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = ["key", "name"]


class _PerformanceComputeTaskSerializer(serializers.ModelSerializer):

    data_manager_key = serializers.UUIDField(format="hex_verbose", source="data_manager_id")
    algo_key = serializers.UUIDField(format="hex_verbose", source="algo_id")
    epoch = serializers.SerializerMethodField()
    round_idx = serializers.SerializerMethodField()

    class Meta:
        model = ComputeTask
        fields = [
            "key",
            "data_manager_key",
            "algo_key",
            "rank",
            "epoch",
            "round_idx",
            "data_samples",
            "worker",
        ]

    def get_epoch(self, instance):
        return instance.metadata.get("epoch")

    def get_round_idx(self, instance):
        return instance.metadata.get("round_idx")


class CPPerformanceSerializer(serializers.ModelSerializer):
    compute_task = _PerformanceComputeTaskSerializer(read_only=True)
    metric = _PerformanceMetricSerializer(read_only=True)
    perf = serializers.FloatField(source="value")

    class Meta:
        model = Performance
        fields = [
            "compute_task",
            "metric",
            "perf",
        ]

from rest_framework import serializers

from api.models import Algo
from api.models import AlgoOutput
from api.models import ComputeTask
from api.models import Performance
from api.serializers.utils import SafeSerializerMixin
from orchestrator import common_pb2


class PerformanceSerializer(serializers.ModelSerializer, SafeSerializerMixin):

    # overwrite primary key field for the SafeSerializerMixin check
    # the unique constraint for compute_task_key + metric_key in the model
    # ensures no duplicates are created
    primary_key_name = "id"

    compute_task_key = serializers.PrimaryKeyRelatedField(
        queryset=ComputeTask.objects.all(), source="compute_task", pk_field=serializers.UUIDField(format="hex_verbose")
    )

    metric_key = serializers.PrimaryKeyRelatedField(
        queryset=Algo.objects.all(), source="metric", pk_field=serializers.UUIDField(format="hex_verbose")
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
    output_identifier = serializers.SerializerMethodField()

    class Meta:
        model = Algo
        fields = ["key", "name", "output_identifier"]

    def get_output_identifier(self, obj):
        try:
            performance_output = AlgoOutput.objects.get(
                algo_id=obj.key, kind=common_pb2.AssetKind.Name(common_pb2.ASSET_PERFORMANCE)
            )
        except (AlgoOutput.MultipleObjectsReturned, AlgoOutput.DoesNotExist) as e:
            raise Exception(f"Couldn't associate an output identifier to performance for algo '{obj.key}', error : {e}")

        return performance_output.identifier


class _PerformanceComputeTaskSerializer(serializers.ModelSerializer):
    data_manager_key = serializers.UUIDField(format="hex_verbose", source="data_manager_id")
    algo_key = serializers.UUIDField(format="hex_verbose", source="algo_id")
    round_idx = serializers.SerializerMethodField()

    class Meta:
        model = ComputeTask
        fields = [
            "key",
            "data_manager_key",
            "algo_key",
            "rank",
            "round_idx",
            "data_samples",
            "worker",
        ]

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


class ExportPerformanceSerializer(serializers.ModelSerializer):
    compute_plan_key = serializers.UUIDField()
    compute_plan_name = serializers.CharField()
    compute_plan_tag = serializers.CharField()
    compute_plan_status = serializers.CharField()
    compute_plan_start_date = serializers.DateTimeField()
    compute_plan_end_date = serializers.DateTimeField()
    compute_plan_metadata = serializers.JSONField()
    metric_name = serializers.CharField()
    worker = serializers.CharField()
    test_task_rank = serializers.IntegerField()
    test_task_round = serializers.IntegerField()
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
            "metric_name",
            "worker",
            "test_task_rank",
            "test_task_round",
            "performance",
        ]

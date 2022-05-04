from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.failure_report_pb2 as failure_report_pb2
from localrep.models import Algo
from localrep.models import ComputePlan
from localrep.models import ComputeTask
from localrep.models import DataManager
from localrep.models import DataSample
from localrep.models.computetask import TaskDataSamples
from localrep.serializers.algo import AlgoSerializer
from localrep.serializers.datamanager import DataManagerSerializer
from localrep.serializers.model import ModelSerializer
from localrep.serializers.performance import PerformanceSerializer
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from localrep.serializers.utils import make_addressable_serializer
from localrep.serializers.utils import make_download_process_permission_serializer
from localrep.serializers.utils import make_permission_serializer
from substrapp.compute_tasks.context import TASK_DATA_FIELD
from substrapp.compute_tasks.errors import ComputeTaskErrorType

TASK_CATEGORY_FIELDS = {
    computetask_pb2.TASK_TRAIN: "train",
    computetask_pb2.TASK_TEST: "test",
    computetask_pb2.TASK_COMPOSITE: "composite",
    computetask_pb2.TASK_AGGREGATE: "aggregate",
}


class CategoryField(serializers.Field):
    def to_representation(self, instance):
        return computetask_pb2.ComputeTaskCategory.Name(instance)

    def to_internal_value(self, data):
        return computetask_pb2.ComputeTaskCategory.Value(data)


class StatusField(serializers.Field):
    def to_representation(self, instance):
        return computetask_pb2.ComputeTaskStatus.Name(instance)

    def to_internal_value(self, data):
        return computetask_pb2.ComputeTaskStatus.Value(data)


class ErrorTypeField(serializers.Field):
    def to_representation(self, instance):
        return failure_report_pb2.ErrorType.Name(instance)

    def to_internal_value(self, data):
        return failure_report_pb2.ErrorType.Value(data)


class AlgoField(serializers.Field):
    def to_representation(self, data):
        return AlgoSerializer(instance=data).data

    def to_internal_value(self, data):
        return Algo.objects.get(key=data["key"])


class TestTaskSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["perfs"] = {perf["metric_key"]: perf["performance_value"] for perf in data["perfs"]} or None
        return data

    data_manager_key = serializers.PrimaryKeyRelatedField(
        queryset=DataManager.objects.all(),
        source="data_manager",
        required=False,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    data_sample_keys = serializers.PrimaryKeyRelatedField(
        queryset=DataSample.objects.all(),
        source="data_samples",
        many=True,
        required=False,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    metric_keys = serializers.PrimaryKeyRelatedField(
        queryset=Algo.objects.all(),
        many=True,
        source="metrics",
        required=False,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    perfs = PerformanceSerializer(many=True, read_only=True, source="performances")

    class Meta:
        fields = ["data_manager_key", "data_sample_keys", "metric_keys", "perfs"]


class TrainTaskSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["models"] = data["models"] or None  # sdk does not support empty list
        return data

    data_manager_key = serializers.PrimaryKeyRelatedField(
        queryset=DataManager.objects.all(),
        source="data_manager",
        required=False,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    data_sample_keys = serializers.PrimaryKeyRelatedField(
        queryset=DataSample.objects.all(),
        source="data_samples",
        many=True,
        required=False,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    model_permissions = make_download_process_permission_serializer("model_")(source="*", required=False)
    models = ModelSerializer(many=True, read_only=True)

    class Meta:
        fields = ["data_manager_key", "data_sample_keys", "model_permissions", "models"]


class AggregateTaskSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["models"] = data["models"] or None  # sdk does not support empty list
        return data

    model_permissions = make_download_process_permission_serializer("model_")(source="*", required=False)
    models = ModelSerializer(many=True, read_only=True)

    class Meta:
        fields = ["model_permissions", "models"]


class CompositeTaskSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["models"] = data["models"] or None  # sdk does not support empty list
        return data

    data_manager_key = serializers.PrimaryKeyRelatedField(
        queryset=DataManager.objects.all(),
        source="data_manager",
        required=False,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )

    data_sample_keys = serializers.PrimaryKeyRelatedField(
        queryset=DataSample.objects.all(),
        source="data_samples",
        many=True,
        required=False,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    models = ModelSerializer(many=True, read_only=True)
    head_permissions = make_download_process_permission_serializer("head_")(source="*", required=False)
    trunk_permissions = make_download_process_permission_serializer("trunk_")(source="*", required=False)

    class Meta:
        fields = ["data_manager_key", "data_sample_keys", "models", "head_permissions", "trunk_permissions"]


class ComputeTaskSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    category = CategoryField()
    status = StatusField()
    error_type = ErrorTypeField(required=False)
    logs_permission = make_permission_serializer("logs_permission")(source="*")
    logs_address = make_addressable_serializer("logs")(source="*", required=False)
    algo = AlgoField()

    # Need to set `pk_field` for `PrimaryKeyRelatedField` in order to correctly serialize `UUID` to `str`
    # See: https://stackoverflow.com/a/51636009
    compute_plan_key = serializers.PrimaryKeyRelatedField(
        queryset=ComputePlan.objects.all(),
        source="compute_plan",
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    parent_task_keys = serializers.ListField(source="parent_tasks", child=serializers.CharField(), required=False)
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)

    data_manager_key = serializers.PrimaryKeyRelatedField(
        queryset=DataManager.objects.all(),
        source="data_manager",
        required=False,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    data_sample_keys = serializers.PrimaryKeyRelatedField(
        queryset=DataSample.objects.all(),
        source="data_samples",
        many=True,
        required=False,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )

    model_permissions = make_download_process_permission_serializer("model_")(source="*", required=False)
    head_permissions = make_download_process_permission_serializer("head_")(source="*", required=False)
    trunk_permissions = make_download_process_permission_serializer("trunk_")(source="*", required=False)

    test = TestTaskSerializer(required=False, source="*")
    train = TrainTaskSerializer(required=False, source="*")
    aggregate = AggregateTaskSerializer(required=False, source="*")
    composite = CompositeTaskSerializer(required=False, source="*")

    @transaction.atomic
    def create(self, validated_data):
        if "data_samples" not in validated_data:
            # aggregate task do not have data samples
            return super().create(validated_data)

        data_samples = validated_data.pop("data_samples")
        compute_task = super().create(validated_data)
        for order, data_sample in enumerate(data_samples):
            TaskDataSamples.objects.create(compute_task=compute_task, data_sample=data_sample, order=order)
        compute_task.refresh_from_db()
        return compute_task

    def to_representation(self, instance):
        data = super().to_representation(instance)

        for category, field in TASK_CATEGORY_FIELDS.items():
            if instance.category != category:
                del data[field]

        del data["data_manager_key"]
        del data["data_sample_keys"]
        del data["model_permissions"]
        del data["head_permissions"]
        del data["trunk_permissions"]
        del data["logs_address"]
        del data["logs_owner"]

        # error_type
        if data["error_type"] is not None:
            data["error_type"] = ComputeTaskErrorType.from_int(
                failure_report_pb2.ErrorType.Value(data["error_type"])
            ).name

        # replace storage addresses
        self._replace_storage_addresses(data)

        return data

    def _replace_storage_addresses(self, task):
        request = self.context.get("request")
        if not request:
            return task

        # replace in common relationships

        if "algo" in task:
            task["algo"]["description"]["storage_address"] = request.build_absolute_uri(
                reverse("substrapp:algo-description", args=[task["algo"]["key"]])
            )
            task["algo"]["algorithm"]["storage_address"] = request.build_absolute_uri(
                reverse("substrapp:algo-file", args=[task["algo"]["key"]])
            )

        # replace in category-dependent relationships

        category = computetask_pb2.ComputeTaskCategory.Value(task["category"])
        task_details = task[TASK_DATA_FIELD[category]]

        if "data_manager" in task_details and task_details["data_manager"]:
            data_manager = task_details["data_manager"]
            data_manager["description"]["storage_address"] = request.build_absolute_uri(
                reverse("substrapp:data_manager-description", args=[data_manager["key"]])
            )
            data_manager["opener"]["storage_address"] = request.build_absolute_uri(
                reverse("substrapp:data_manager-opener", args=[data_manager["key"]])
            )

        models = task_details.get("models") or []  # field may be set to None
        for model in models:
            if "address" in model and model["address"]:
                model["address"]["storage_address"] = request.build_absolute_uri(
                    reverse("substrapp:model-file", args=[model["key"]])
                )

        for metric in task_details.get("metrics", []):
            metric["description"]["storage_address"] = request.build_absolute_uri(
                reverse("substrapp:algo-description", args=[metric["key"]])
            )
            metric["algorithm"]["storage_address"] = request.build_absolute_uri(
                reverse("substrapp:algo-algorithm", args=[metric["key"]])
            )

    class Meta:
        model = ComputeTask
        fields = [
            "aggregate",
            "algo",
            "category",
            "channel",
            "composite",
            "compute_plan_key",
            "creation_date",
            "data_manager_key",
            "data_sample_keys",
            "end_date",
            "error_type",
            "head_permissions",
            "key",
            "logs_address",
            "logs_owner",
            "logs_permission",
            "metadata",
            "model_permissions",
            "owner",
            "parent_task_keys",
            "rank",
            "start_date",
            "status",
            "tag",
            "test",
            "train",
            "trunk_permissions",
            "worker",
        ]


TASK_FIELD = {
    computetask_pb2.TASK_TRAIN: "train",
    computetask_pb2.TASK_TEST: "test",
    computetask_pb2.TASK_AGGREGATE: "aggregate",
    computetask_pb2.TASK_COMPOSITE: "composite",
}


class ComputeTaskWithRelationshipsSerializer(ComputeTaskSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.category in [computetask_pb2.TASK_TRAIN, computetask_pb2.TASK_TEST, computetask_pb2.TASK_COMPOSITE]:
            data_manager = DataManager.objects.get(
                key=data[TASK_FIELD[instance.category]]["data_manager_key"],
                channel=instance.channel,
            )
            data[TASK_FIELD[instance.category]]["data_manager"] = DataManagerSerializer(data_manager).data

        if instance.category == computetask_pb2.TASK_TEST:
            metrics = Algo.objects.filter(
                key__in=data[TASK_FIELD[instance.category]]["metric_keys"],
                channel=instance.channel,
            ).order_by("creation_date", "key")
            data[TASK_FIELD[instance.category]]["metrics"] = AlgoSerializer(metrics, many=True).data

        # parent_tasks
        parent_tasks = ComputeTask.objects.filter(
            key__in=data["parent_task_keys"],
            channel=instance.channel,
        ).order_by("creation_date", "key")
        data["parent_tasks"] = ComputeTaskSerializer(parent_tasks, many=True).data
        for parent_task in data.get("parent_tasks", []):
            self._replace_storage_addresses(parent_task)
        return data

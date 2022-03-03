import copy

from rest_framework import serializers

import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.failure_report_pb2 as failure_report_pb2
from localrep.models import Algo
from localrep.models import ComputePlan
from localrep.models import ComputeTask
from localrep.models import DataManager
from localrep.models import Metric
from localrep.serializers.algo import AlgoSerializer
from localrep.serializers.model import ModelSerializer
from localrep.serializers.performance import PerformanceSerializer
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from localrep.serializers.utils import make_addressable_serializer
from localrep.serializers.utils import make_download_process_permission_serializer
from localrep.serializers.utils import make_permission_serializer


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


class ComputeTaskSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    category = CategoryField()
    status = StatusField()
    error_type = ErrorTypeField(required=False)
    logs_permission = make_permission_serializer("logs_permission")(source="*")
    logs_address = make_addressable_serializer("logs")(source="*", required=False)

    algo = AlgoField()
    models = ModelSerializer(many=True, read_only=True)
    perfs = PerformanceSerializer(many=True, read_only=True, source="performances")

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
    data_sample_keys = serializers.ListField(source="data_samples", child=serializers.CharField(), required=False)
    metric_keys = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all(),
        many=True,
        source="metrics",
        required=False,
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    model_permissions = make_download_process_permission_serializer("model_")(source="*", required=False)
    head_permissions = make_download_process_permission_serializer("head_")(source="*", required=False)
    trunk_permissions = make_download_process_permission_serializer("trunk_")(source="*", required=False)

    def __init__(self, *args, **kwargs):
        # FIXME: quick optimization to avoid useless DB queries, to replace by category based serializers
        category = kwargs.pop("category", None)
        super().__init__(*args, **kwargs)
        if category is not None:
            if category == "testtuple":
                self.fields.pop("models")
            else:
                self.fields.pop("perfs")
                self.fields.pop("metric_keys")

    def to_internal_value(self, data):
        prepared_data = copy.deepcopy(data)
        task_category = computetask_pb2.ComputeTaskCategory.Value(data["category"])
        if task_category == computetask_pb2.TASK_TRAIN:
            prepared_data["data_manager_key"] = data["train"]["data_manager_key"]
            prepared_data["data_sample_keys"] = data["train"]["data_sample_keys"]
            prepared_data["model_permissions"] = data["train"]["model_permissions"]
        elif task_category == computetask_pb2.TASK_TEST:
            prepared_data["data_manager_key"] = data["test"]["data_manager_key"]
            prepared_data["data_sample_keys"] = data["test"]["data_sample_keys"]
            prepared_data["metric_keys"] = data["test"]["metric_keys"]
        elif task_category == computetask_pb2.TASK_AGGREGATE:
            prepared_data["model_permissions"] = data["aggregate"]["model_permissions"]
        elif task_category == computetask_pb2.TASK_COMPOSITE:
            prepared_data["data_manager_key"] = data["composite"]["data_manager_key"]
            prepared_data["data_sample_keys"] = data["composite"]["data_sample_keys"]
            prepared_data["head_permissions"] = data["composite"]["head_permissions"]
            prepared_data["trunk_permissions"] = data["composite"]["trunk_permissions"]
        return super().to_internal_value(prepared_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.category == computetask_pb2.TASK_TRAIN:
            data["train"] = {
                "data_manager_key": data["data_manager_key"],
                "data_sample_keys": data["data_sample_keys"],
                "model_permissions": data["model_permissions"],
                "models": data["models"] or None,  # sdk does not support empty list
            }
        elif instance.category == computetask_pb2.TASK_TEST:
            data["test"] = {
                "data_manager_key": data["data_manager_key"],
                "data_sample_keys": data["data_sample_keys"],
                "metric_keys": data["metric_keys"],
                "perfs": {perf["metric_key"]: perf["performance_value"] for perf in data["perfs"]} or None,
            }
        elif instance.category == computetask_pb2.TASK_AGGREGATE:
            data["aggregate"] = {
                "model_permissions": data["model_permissions"],
                "models": data["models"] or None,
            }
        elif instance.category == computetask_pb2.TASK_COMPOSITE:
            data["composite"] = {
                "data_manager_key": data["data_manager_key"],
                "data_sample_keys": data["data_sample_keys"],
                "head_permissions": data["head_permissions"],
                "trunk_permissions": data["trunk_permissions"],
                "models": data["models"] or None,
            }
        del data["data_manager_key"]
        del data["data_sample_keys"]
        del data["model_permissions"]
        del data["head_permissions"]
        del data["trunk_permissions"]
        del data["logs_address"]
        del data["logs_owner"]
        # fields could be removed at init
        if "models" in data:
            del data["models"]
        if "perfs" in data:
            del data["perfs"]
        if "metric_keys" in data:
            del data["metric_keys"]

        return data

    class Meta:
        model = ComputeTask
        fields = [
            "algo",
            "category",
            "channel",
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
            "metric_keys",
            "model_permissions",
            "models",
            "owner",
            "parent_task_keys",
            "perfs",
            "rank",
            "start_date",
            "status",
            "tag",
            "trunk_permissions",
            "worker",
        ]

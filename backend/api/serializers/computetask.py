from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

import orchestrator.failure_report_pb2 as failure_report_pb2
from api.models import ComputePlan
from api.models import ComputeTask
from api.models import ComputeTaskInput
from api.models import ComputeTaskInputAsset
from api.models import ComputeTaskOutput
from api.models import ComputeTaskOutputAsset
from api.models import DataManager
from api.models import DataSample
from api.models import Function
from api.models import FunctionInput
from api.models import FunctionOutput
from api.models import Model
from api.models import Performance
from api.serializers.datamanager import DataManagerSerializer
from api.serializers.datasample import DataSampleSerializer
from api.serializers.function import FunctionSerializer
from api.serializers.model import ModelSerializer
from api.serializers.performance import PerformanceSerializer
from api.serializers.utils import SafeSerializerMixin
from api.serializers.utils import get_channel_choices
from api.serializers.utils import make_download_process_permission_serializer
from api.serializers.utils import make_permission_serializer
from substrapp.compute_tasks.errors import ComputeTaskErrorType


class ComputeTaskInputSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    class Meta:
        model = ComputeTaskInput
        fields = [
            "identifier",
            "asset_key",
            "parent_task_key",
            "parent_task_output_identifier",
            "asset",
        ]

    asset = serializers.SerializerMethodField(source="*", read_only=True)

    def to_representation(self, data):
        data = super().to_representation(data)
        asset_data = data.pop("asset")
        data.update(asset_data)
        return data

    def get_asset(self, task_input):
        data = {}
        try:
            if task_input.asset.asset_kind == FunctionInput.Kind.ASSET_DATA_MANAGER:
                data_manager = DataManager.objects.get(key=task_input.asset.asset_key)
                data_manager_data = DataManagerSerializer(context=self.context, instance=data_manager).data
                data["addressable"] = data_manager_data["opener"]
                data["permissions"] = data_manager_data["permissions"]
            elif task_input.asset.asset_kind == FunctionInput.Kind.ASSET_MODEL:
                model = Model.objects.get(key=task_input.asset.asset_key)
                model_data = ModelSerializer(context=self.context, instance=model).data
                data["addressable"] = model_data["address"]
                data["permissions"] = model_data["permissions"]
        except ComputeTaskInputAsset.DoesNotExist:
            pass
        return data


class ComputeTaskOutputSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    class Meta:
        model = ComputeTaskOutput
        fields = [
            "identifier",
            "permissions",
            "transient",
            "value",
        ]

    permissions = make_download_process_permission_serializer()(source="*")
    value = serializers.SerializerMethodField(source="*", read_only=True)

    def get_value(self, task_output):
        data = []
        for output_asset in task_output.assets.all():
            if output_asset.asset_kind == FunctionOutput.Kind.ASSET_MODEL:
                model = Model.objects.get(key=output_asset.asset_key)
                data.append(ModelSerializer(context=self.context, instance=model).data)
            elif output_asset.asset_kind == FunctionOutput.Kind.ASSET_PERFORMANCE:
                _, metric_key = output_asset.asset_key.split("|")
                perf = Performance.objects.get(compute_task_output=output_asset.task_output, metric__key=metric_key)
                data.append(perf.value)

        # FIXME: we should better always return a list,
        # but it may requires some adapations on the frontend side
        if len(data) == 0:
            return None
        elif len(data) == 1:
            return data[0]
        else:
            return data


class ComputeTaskInputAssetSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    identifier = serializers.SerializerMethodField(source="*", read_only=True)
    kind = serializers.CharField(source="asset_kind", read_only=True)
    asset = serializers.SerializerMethodField(source="*", read_only=True)

    class Meta:
        model = ComputeTaskInputAsset
        fields = [
            "identifier",
            "kind",
            "asset",
        ]

    def get_identifier(self, task_input_asset):
        return task_input_asset.task_input.identifier

    def get_asset(self, task_input_asset):
        if task_input_asset.asset_kind == FunctionInput.Kind.ASSET_DATA_SAMPLE:
            data_sample = DataSample.objects.get(key=task_input_asset.asset_key)
            return DataSampleSerializer(context=self.context, instance=data_sample).data
        elif task_input_asset.asset_kind == FunctionInput.Kind.ASSET_DATA_MANAGER:
            data_manager = DataManager.objects.get(key=task_input_asset.asset_key)
            return DataManagerSerializer(context=self.context, instance=data_manager).data
        elif task_input_asset.asset_kind == FunctionInput.Kind.ASSET_MODEL:
            model = Model.objects.get(key=task_input_asset.asset_key)
            return ModelSerializer(context=self.context, instance=model).data


class ComputeTaskOutputAssetSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    identifier = serializers.SerializerMethodField(source="*", read_only=True)
    kind = serializers.CharField(source="asset_kind", read_only=True)
    asset = serializers.SerializerMethodField(source="*", read_only=True)

    class Meta:
        model = ComputeTaskOutputAsset
        fields = [
            "identifier",
            "kind",
            "asset",
        ]

    def get_identifier(self, task_output_asset):
        return task_output_asset.task_output.identifier

    def get_asset(self, task_output_asset):
        if task_output_asset.asset_kind == FunctionOutput.Kind.ASSET_MODEL:
            model = Model.objects.get(key=task_output_asset.asset_key)
            return ModelSerializer(context=self.context, instance=model).data
        elif task_output_asset.asset_kind == FunctionOutput.Kind.ASSET_PERFORMANCE:
            _, metric_key = task_output_asset.asset_key.split("|")
            performance = Performance.objects.get(
                compute_task_output=task_output_asset.task_output, metric__key=metric_key
            )
            return PerformanceSerializer(context=self.context, instance=performance).data


class FunctionField(serializers.Field):
    def to_representation(self, data):
        return FunctionSerializer(instance=data).data

    def to_internal_value(self, data):
        return Function.objects.get(key=data["key"])


class ComputeTaskSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    logs_permission = make_permission_serializer("logs_permission")(source="*")
    function = FunctionField()

    # Need to set `pk_field` for `PrimaryKeyRelatedField` in order to correctly serialize `UUID` to `str`
    # See: https://stackoverflow.com/a/51636009
    compute_plan_key = serializers.PrimaryKeyRelatedField(
        queryset=ComputePlan.objects.all(),
        source="compute_plan",
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)

    duration = serializers.IntegerField(read_only=True)

    class Meta:
        model = ComputeTask
        fields = [
            "function",
            "channel",
            "compute_plan_key",
            "creation_date",
            "end_date",
            "error_type",
            "key",
            "logs_permission",
            "metadata",
            "owner",
            "rank",
            "start_date",
            "status",
            "tag",
            "worker",
            "duration",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

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
        if "function" in task:
            task["function"]["description"]["storage_address"] = request.build_absolute_uri(
                reverse("api:function-description", args=[task["function"]["key"]])
            )
            task["function"]["function"]["storage_address"] = request.build_absolute_uri(
                reverse("api:function-file", args=[task["function"]["key"]])
            )


class ComputeTaskWithDetailsSerializer(ComputeTaskSerializer):
    inputs = ComputeTaskInputSerializer(many=True)
    outputs = ComputeTaskOutputSerializer(many=True)

    class Meta:
        model = ComputeTask
        fields = ComputeTaskSerializer.Meta.fields + [
            "inputs",
            "outputs",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["outputs"] = {_output.pop("identifier"): _output for _output in data["outputs"]}

        return data

    @transaction.atomic
    def create(self, validated_data):
        inputs = validated_data.pop("inputs")
        outputs = validated_data.pop("outputs")

        compute_task = super().create(validated_data)
        input_kinds = {
            function_input.identifier: function_input.kind for function_input in compute_task.function.inputs.all()
        }

        for position, input in enumerate(inputs):
            task_input = ComputeTaskInput.objects.create(
                channel=compute_task.channel,
                task=compute_task,
                position=position,
                **input,
            )
            # task input asset could be known during task registration
            # or could be resolved later if it does not exist yet
            if task_input.asset_key:
                ComputeTaskInputAsset.objects.create(
                    channel=compute_task.channel,
                    task_input=task_input,
                    asset_key=task_input.asset_key,
                    asset_kind=input_kinds[task_input.identifier],
                )
            elif task_input.parent_task_key:
                task_output = ComputeTaskOutput.objects.get(
                    task=task_input.parent_task_key,
                    identifier=task_input.parent_task_output_identifier,
                )
                # this only supports a single asset per output for now
                task_output_asset = task_output.assets.first()
                if task_output_asset:
                    ComputeTaskInputAsset.objects.create(
                        channel=compute_task.channel,
                        task_input=task_input,
                        asset_key=task_output_asset.asset_key,
                        asset_kind=input_kinds[task_input.identifier],
                    )

        for output in outputs:
            ComputeTaskOutput.objects.create(
                channel=compute_task.channel,
                task=compute_task,
                **output,
            )

        compute_task.refresh_from_db()
        return compute_task

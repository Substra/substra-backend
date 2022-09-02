from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

import orchestrator.common_pb2 as common_pb2
import orchestrator.failure_report_pb2 as failure_report_pb2
from localrep.models import Algo
from localrep.models import ComputePlan
from localrep.models import ComputeTask
from localrep.models import ComputeTaskInput
from localrep.models import ComputeTaskOutput
from localrep.models import DataManager
from localrep.models import DataSample
from localrep.models import Model
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
from substrapp.compute_tasks.errors import ComputeTaskErrorType

TASK_CATEGORY_FIELDS = {
    ComputeTask.Category.TASK_TRAIN: "train",
    ComputeTask.Category.TASK_PREDICT: "predict",
    ComputeTask.Category.TASK_TEST: "test",
    ComputeTask.Category.TASK_COMPOSITE: "composite",
    ComputeTask.Category.TASK_AGGREGATE: "aggregate",
}

OUTPUT_MODEL_CATEGORY = {
    "model": "MODEL_SIMPLE",
    "predictions": "MODEL_SIMPLE",
    "shared": "MODEL_SIMPLE",
    "local": "MODEL_HEAD",
}


class ComputeTaskInputSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    class Meta:
        model = ComputeTaskInput
        fields = [
            "identifier",
            "asset_key",
            "parent_task_key",
            "parent_task_output_identifier",
        ]


class ComputeTaskOutputSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    class Meta:
        model = ComputeTaskOutput
        fields = [
            "identifier",
            "permissions",
            "transient",
        ]

    permissions = make_download_process_permission_serializer()(source="*")


class AlgoField(serializers.Field):
    def to_representation(self, data):
        return AlgoSerializer(instance=data).data

    def to_internal_value(self, data):
        return Algo.objects.get(key=data["key"])


class PredictTaskSerializer(serializers.Serializer):
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

    class Meta:
        fields = ["data_manager_key", "data_sample_keys", "models"]


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
    perfs = PerformanceSerializer(many=True, read_only=True, source="performances")

    class Meta:
        fields = ["data_manager_key", "data_sample_keys", "perfs"]


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
    models = ModelSerializer(many=True, read_only=True)

    class Meta:
        fields = ["data_manager_key", "data_sample_keys", "models"]


class AggregateTaskSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["models"] = data["models"] or None  # sdk does not support empty list
        return data

    models = ModelSerializer(many=True, read_only=True)

    class Meta:
        fields = ["models"]


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

    class Meta:
        fields = ["data_manager_key", "data_sample_keys", "models"]


class ComputeTaskSerializer(serializers.ModelSerializer, SafeSerializerMixin):
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

    predict = PredictTaskSerializer(required=False, source="*")
    test = TestTaskSerializer(required=False, source="*")
    train = TrainTaskSerializer(required=False, source="*")
    aggregate = AggregateTaskSerializer(required=False, source="*")
    composite = CompositeTaskSerializer(required=False, source="*")

    duration = serializers.IntegerField(read_only=True)
    inputs = ComputeTaskInputSerializer(many=True)
    outputs = ComputeTaskOutputSerializer(many=True)

    @transaction.atomic
    def create(self, validated_data):
        data_samples = []
        if "data_samples" in validated_data:
            data_samples = validated_data.pop("data_samples")

        inputs = validated_data.pop("inputs")
        outputs = validated_data.pop("outputs")

        compute_task = super().create(validated_data)

        for order, data_sample in enumerate(data_samples):
            TaskDataSamples.objects.create(compute_task=compute_task, data_sample=data_sample, order=order)

        for position, input in enumerate(inputs):
            ComputeTaskInput.objects.create(task=compute_task, position=position, **input)

        for output in outputs:
            ComputeTaskOutput.objects.create(task=compute_task, **output)

        compute_task.refresh_from_db()
        return compute_task

    def to_representation(self, instance):  # noqa: C901
        # TODO: Rework this function which is too complex according to C901
        # It will be soon rewritten with generic task and the removing of the legacy fields
        data = super().to_representation(instance)

        for category, field in TASK_CATEGORY_FIELDS.items():
            if instance.category != category:
                del data[field]

        del data["data_manager_key"]
        del data["data_sample_keys"]
        del data["logs_address"]
        del data["logs_owner"]

        # error_type
        if data["error_type"] is not None:
            data["error_type"] = ComputeTaskErrorType.from_int(
                failure_report_pb2.ErrorType.Value(data["error_type"])
            ).name

        # replace storage addresses
        self._replace_storage_addresses(data)

        data["outputs"] = {_output.pop("identifier"): _output for _output in data["outputs"]}

        # Fill the legacy permission fields.
        # This block will be deleted once all clients have stopped using these legacy permissions fields.
        if instance.category in [ComputeTask.Category.TASK_TRAIN, ComputeTask.Category.TASK_AGGREGATE]:
            data[TASK_CATEGORY_FIELDS[instance.category]]["model_permissions"] = data["outputs"]["model"]["permissions"]
        elif instance.category == ComputeTask.Category.TASK_COMPOSITE:
            data[TASK_CATEGORY_FIELDS[instance.category]]["head_permissions"] = data["outputs"]["local"]["permissions"]
            data[TASK_CATEGORY_FIELDS[instance.category]]["trunk_permissions"] = data["outputs"]["shared"][
                "permissions"
            ]
        elif instance.category == ComputeTask.Category.TASK_PREDICT:
            data[TASK_CATEGORY_FIELDS[instance.category]]["prediction_permissions"] = data["outputs"]["predictions"][
                "permissions"
            ]

        # Include output models/performances in output field
        # TODO: Move this in ComputeTaskOutputSerializer
        #  + Use the actual asset<->output association to find the assets
        #  (should be done once generic task is done)
        for output_id, output in data["outputs"].items():
            output_kind = self._find_output_kind(data, output_id)
            if output_kind == common_pb2.AssetKind.Name(common_pb2.ASSET_MODEL):
                output["value"] = self._find_output_model(instance.category, data, output_id, data["key"])
            elif output_kind == common_pb2.AssetKind.Name(common_pb2.ASSET_PERFORMANCE):
                perfs = data["test"]["perfs"]
                if perfs:
                    if len(perfs) != 1:  # performance output cannot be multiple
                        raise Exception(
                            f"Couldn't associate a performance to output '{output_id}' of task '{data['key']}'"
                        )
                    (value,) = perfs.values()
                else:
                    value = None
                output["value"] = value

        # set data inputs
        self._inputs_to_representation(data)

        return data

    def _inputs_to_representation(self, data):  # noqa: C901
        # Include asset kind and asset addressable if exists in input field
        # TODO: Move this in ComputeTaskInputSerializer
        #  + Use the actual asset<->input association to find the assets
        # to remove C901 complexity warning (should be done once generic task is done)
        for input in data["inputs"]:
            input_kind = self._find_input_kind(data, input.get("identifier"))
            if input_kind == common_pb2.AssetKind.Name(common_pb2.ASSET_DATA_MANAGER):
                input["addressable"] = self._get_opener_addressable(input.get("asset_key"))
                input["permissions"] = self._get_opener_permissions(input.get("asset_key"))

            if input_kind == common_pb2.AssetKind.Name(common_pb2.ASSET_MODEL):
                # get parent task output permissions
                try:
                    outputs = ComputeTaskOutput.objects.filter(task_id=input.get("parent_task_key")).all()
                    models = Model.objects.filter(compute_task_id=input.get("parent_task_key")).all()
                except ObjectDoesNotExist:
                    input["permissions"] = None
                    input["addressable"] = None
                    continue
                else:
                    output_identifier = input.get("parent_task_output_identifier")
                    for output in outputs:
                        if output.identifier == output_identifier:
                            input["permissions"] = make_download_process_permission_serializer()(output).data
                    request = self.context.get("request")
                    if request:
                        for model in models:
                            model_category = OUTPUT_MODEL_CATEGORY[output_identifier]
                            if model.category == model_category:
                                input["addressable"] = make_addressable_serializer("model")(model).data
                                input["addressable"]["storage_address"] = request.build_absolute_uri(
                                    reverse("substrapp:model-file", args=[model.key])
                                )

    def _find_output_kind(self, data, output_id):
        return data["algo"]["outputs"][output_id]["kind"]

    def _find_input_kind(self, data, input_id):
        return data["algo"]["inputs"][input_id]["kind"]

    def _find_output_model(self, instance_category, data, output_identifier, task_key):
        task_category_field = TASK_CATEGORY_FIELDS[instance_category]
        model_category = OUTPUT_MODEL_CATEGORY[output_identifier]
        models = data[task_category_field]["models"]
        if models:  # return None in case the output model is not computed yet
            matching_models = [model for model in models if model["category"] == model_category]
            # Due to how sync works it is possible that one model is present but not the other for composite tasks
            if matching_models:
                if len(matching_models) > 1:  # No task can output more than one model of each category
                    raise Exception(f"Couldn't associate a model to output '{output_identifier}' of task '{task_key}'")
                model = matching_models[0]
                return model

    def _get_opener_addressable(self, key):
        request = self.context.get("request")
        if request:
            try:
                data_manager = DataManager.objects.filter(key=key).get()
            except ObjectDoesNotExist:
                return None
            else:
                addressable = make_addressable_serializer("opener")(data_manager).data
                addressable["storage_address"] = request.build_absolute_uri(
                    reverse("substrapp:data_manager-opener", args=[key])
                )
            return addressable

    def _get_opener_permissions(self, key):
        try:
            data_manager = DataManager.objects.filter(key=key).get()
        except ObjectDoesNotExist:
            return None
        else:
            return make_download_process_permission_serializer()(data_manager).data

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
        task_details = task[TASK_CATEGORY_FIELDS[task["category"]]]

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
            "key",
            "logs_address",
            "logs_owner",
            "logs_permission",
            "metadata",
            "owner",
            "parent_task_keys",
            "rank",
            "start_date",
            "status",
            "tag",
            "predict",
            "test",
            "train",
            "worker",
            "duration",
            "inputs",
            "outputs",
        ]


class ComputeTaskWithRelationshipsSerializer(ComputeTaskSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.category in [
            ComputeTask.Category.TASK_TRAIN,
            ComputeTask.Category.TASK_PREDICT,
            ComputeTask.Category.TASK_TEST,
            ComputeTask.Category.TASK_COMPOSITE,
        ]:
            data_manager = DataManager.objects.get(
                key=data[TASK_CATEGORY_FIELDS[instance.category]]["data_manager_key"],
                channel=instance.channel,
            )
            data[TASK_CATEGORY_FIELDS[instance.category]]["data_manager"] = DataManagerSerializer(data_manager).data

        # we need to call this again because this time, there are values for data_manager
        self._replace_storage_addresses(data)

        # parent_tasks
        parent_tasks = ComputeTask.objects.filter(
            key__in=data["parent_task_keys"],
            channel=instance.channel,
        ).order_by("creation_date", "key")
        data["parent_tasks"] = ComputeTaskSerializer(parent_tasks, many=True).data
        for parent_task in data.get("parent_tasks", []):
            self._replace_storage_addresses(parent_task)
        return data

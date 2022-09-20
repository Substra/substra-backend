from django.urls import reverse
from rest_framework import serializers

from api.models import Algo
from api.models import AlgoInput
from api.models import AlgoOutput
from api.serializers.utils import SafeSerializerMixin
from api.serializers.utils import get_channel_choices
from api.serializers.utils import make_addressable_serializer
from api.serializers.utils import make_download_process_permission_serializer


class AlgoInputSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    class Meta:
        model = AlgoInput
        fields = [
            "identifier",
            "kind",
            "optional",
            "multiple",
        ]


class AlgoOutputSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    class Meta:
        model = AlgoOutput
        fields = [
            "identifier",
            "kind",
            "multiple",
        ]


class AlgoSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    algorithm = make_addressable_serializer("algorithm")(source="*")
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    description = make_addressable_serializer("description")(source="*")
    permissions = make_download_process_permission_serializer()(source="*")
    inputs = AlgoInputSerializer(many=True)
    outputs = AlgoOutputSerializer(many=True)

    class Meta:
        model = Algo
        fields = [
            "algorithm",
            "category",
            "channel",
            "creation_date",
            "description",
            "key",
            "metadata",
            "name",
            "owner",
            "permissions",
            "inputs",
            "outputs",
        ]

    def to_representation(self, instance):
        res = super().to_representation(instance)
        request = self.context.get("request")
        if request:
            res["description"]["storage_address"] = request.build_absolute_uri(
                reverse("api:algo-description", args=[res["key"]])
            )
            res["algorithm"]["storage_address"] = request.build_absolute_uri(
                reverse("api:algo-file", args=[res["key"]])
            )
        # from list to dict, to align with the orchestrator format
        res["inputs"] = {_input.pop("identifier"): _input for _input in res["inputs"]}
        res["outputs"] = {_output.pop("identifier"): _output for _output in res["outputs"]}

        return res

    def to_internal_value(self, data):
        # from dict to list, to use drf nested serializers
        data["inputs"] = [{"identifier": identifier, **_input} for identifier, _input in data["inputs"].items()]
        data["outputs"] = [{"identifier": identifier, **_output} for identifier, _output in data["outputs"].items()]
        return super().to_internal_value(data)

    def create(self, validated_data):
        inputs = validated_data.pop("inputs")
        outputs = validated_data.pop("outputs")
        algo = super().create(validated_data)

        algo_inputs = AlgoInputSerializer(data=inputs, many=True)
        algo_inputs.is_valid(raise_exception=True)
        for algo_input in algo_inputs.validated_data:
            AlgoInput.objects.create(
                channel=algo.channel,
                algo=algo,
                **algo_input,
            )

        algo_outputs = AlgoOutputSerializer(data=outputs, many=True)
        algo_outputs.is_valid(raise_exception=True)
        for algo_output in algo_outputs.validated_data:
            AlgoOutput.objects.create(
                channel=algo.channel,
                algo=algo,
                **algo_output,
            )

        return algo

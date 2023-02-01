from django.urls import reverse
from rest_framework import serializers

from api.models import Function
from api.models import FunctionInput
from api.models import FunctionOutput
from api.serializers.utils import SafeSerializerMixin
from api.serializers.utils import get_channel_choices
from api.serializers.utils import make_addressable_serializer
from api.serializers.utils import make_download_process_permission_serializer


class FunctionInputSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    class Meta:
        model = FunctionInput
        fields = [
            "identifier",
            "kind",
            "optional",
            "multiple",
        ]


class FunctionOutputSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    class Meta:
        model = FunctionOutput
        fields = [
            "identifier",
            "kind",
            "multiple",
        ]


class FunctionSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    function = make_addressable_serializer("function")(source="*")
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    description = make_addressable_serializer("description")(source="*")
    permissions = make_download_process_permission_serializer()(source="*")
    inputs = FunctionInputSerializer(many=True)
    outputs = FunctionOutputSerializer(many=True)

    class Meta:
        model = Function
        fields = [
            "function",
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
                reverse("api:function-description", args=[res["key"]])
            )
            res["function"]["storage_address"] = request.build_absolute_uri(
                reverse("api:function-file", args=[res["key"]])
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
        function = super().create(validated_data)

        function_inputs = FunctionInputSerializer(data=inputs, many=True)
        function_inputs.is_valid(raise_exception=True)
        for function_input in function_inputs.validated_data:
            FunctionInput.objects.create(
                channel=function.channel,
                function=function,
                **function_input,
            )

        function_outputs = FunctionOutputSerializer(data=outputs, many=True)
        function_outputs.is_valid(raise_exception=True)
        for function_output in function_outputs.validated_data:
            FunctionOutput.objects.create(
                channel=function.channel,
                function=function,
                **function_output,
            )

        return function

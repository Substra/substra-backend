from rest_framework import serializers
from rest_framework.fields import DictField, CharField
from substrapp.orchestrator import get_orchestrator_client


class OrchestratorComputePlanSerializer(serializers.Serializer):
    key = serializers.UUIDField()
    tag = serializers.CharField(
        min_length=0,
        max_length=64,
        allow_blank=True,
        required=False,
        allow_null=True
    )
    metadata = DictField(child=CharField(), required=False, allow_null=True)
    delete_intermediary_models = serializers.BooleanField(required=False)

    def get_args(self, validated_data):
        return {
            'key': str(validated_data.get('key')),
            'tag': validated_data.get('tag'),
            'metadata': validated_data.get('metadata'),
            'delete_intermediary_models': validated_data.get('delete_intermediary_models', False),
        }

    def create(self, channel_name, validated_data):
        args = self.get_args(validated_data)
        with get_orchestrator_client(channel_name) as client:
            return client.register_compute_plan(args)

    def update(self, channel_name, validated_data):
        return

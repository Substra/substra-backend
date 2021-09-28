from rest_framework import serializers
from rest_framework.fields import CharField, DictField
from rest_framework.reverse import reverse

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Objective

from django.conf import settings
from substrapp.utils import get_hash
from substrapp.serializers.utils import FileValidator, PermissionsSerializer

from substrapp.orchestrator import get_orchestrator_client


class ObjectiveSerializer(DynamicFieldsModelSerializer):
    metrics = serializers.FileField(validators=[FileValidator()])

    class Meta:
        model = Objective
        fields = '__all__'


class OrchestratorObjectiveSerializer(serializers.Serializer):
    data_sample_keys = serializers.ListField(child=serializers.UUIDField(), min_length=0, required=False)
    name = serializers.CharField(min_length=1, max_length=100)
    data_manager_key = serializers.UUIDField(required=False, allow_null=True)
    permissions = PermissionsSerializer()
    metrics_name = serializers.CharField(min_length=1, max_length=100)
    metadata = DictField(child=CharField(), required=False, allow_null=True)

    def create(self, channel_name, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        metrics_name = validated_data.get('metrics_name')
        permissions = validated_data.get('permissions')
        data_manager_key = validated_data.get('data_manager_key')
        data_sample_keys = validated_data.get('data_sample_keys')
        metadata = validated_data.get('metadata')

        current_site = settings.DEFAULT_DOMAIN

        args = {
            'key': str(instance.key),
            'name': name,
            'description': {
                'checksum': get_hash(instance.description),
                'storage_address': current_site + reverse('substrapp:objective-description', args=[instance.key])
            },
            'metrics_name': metrics_name,
            'metrics': {
                'checksum': get_hash(instance.metrics),
                'storage_address': current_site + reverse('substrapp:objective-metrics', args=[instance.key])
            },
            'data_manager_key': str(data_manager_key) if data_manager_key else "",
            'data_sample_keys': [str(key) for key in data_sample_keys],
            'new_permissions': {
                'public': permissions.get('public'),
                'authorized_ids': permissions.get('authorized_ids'),
            },
            'metadata': metadata
        }

        with get_orchestrator_client(channel_name) as client:
            return client.register_objective(args)

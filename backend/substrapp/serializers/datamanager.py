from rest_framework import serializers
from rest_framework.fields import CharField, DictField
from rest_framework.reverse import reverse

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import DataManager

from django.conf import settings
from substrapp.utils import get_hash
from substrapp.serializers.utils import PermissionsSerializer

from substrapp.orchestrator import get_orchestrator_client


class DataManagerSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = DataManager
        fields = '__all__'


class OrchestratorDataManagerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=30)
    objective_key = serializers.UUIDField(required=False, allow_null=True)
    permissions = PermissionsSerializer()
    metadata = DictField(child=CharField(), required=False, allow_null=True)

    def create(self, channel_name, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        data_type = validated_data.get('type')
        permissions = validated_data.get('permissions')
        objective_key = validated_data.get('objective_key')
        metadata = validated_data.get('metadata')

        current_site = settings.DEFAULT_DOMAIN

        args = {
            'key': str(instance.key),
            'name': name,
            'opener': {
                'checksum': get_hash(instance.data_opener),
                'storage_address': current_site + reverse('substrapp:data_manager-opener', args=[instance.key])
            },
            'type': data_type,
            'description': {
                'checksum': get_hash(instance.description),
                'storage_address': current_site + reverse('substrapp:data_manager-description', args=[instance.key])
            },
            'objective_key': str(objective_key) if objective_key else "",
            'new_permissions': {
                'public': permissions.get('public'),
                'authorized_ids': permissions.get('authorized_ids'),
            },
            'metadata': metadata
        }

        with get_orchestrator_client(channel_name) as client:
            return client.register_datamanager(args)

from rest_framework import serializers
from rest_framework.fields import CharField, DictField, IntegerField
from rest_framework.reverse import reverse

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Algo

from django.conf import settings
from substrapp.utils import get_hash
from substrapp.serializers.utils import FileValidator, PermissionsSerializer

from substrapp.orchestrator import get_orchestrator_client


class AlgoSerializer(DynamicFieldsModelSerializer):
    file = serializers.FileField(validators=[FileValidator()])

    class Meta:
        model = Algo
        fields = '__all__'


class OrchestratorAlgoSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=100)
    permissions = PermissionsSerializer()
    metadata = DictField(child=CharField(), required=False, allow_null=True)
    category = IntegerField(min_value=0, max_value=3)

    def create(self, channel_name, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        permissions = validated_data.get('permissions')
        metadata = validated_data.get('metadata')
        category = validated_data.get('category')

        current_site = settings.DEFAULT_DOMAIN

        args = {
            'key': str(instance.key),
            'name': name,
            'category': category,
            'description': {
                'checksum': get_hash(instance.description),
                'storage_address': current_site + reverse('substrapp:algo-description', args=[instance.key]),
            },
            'algorithm': {
                'checksum': get_hash(instance.file),
                'storage_address': current_site + reverse('substrapp:algo-file', args=[instance.key]),
            },
            'new_permissions': {
                'public': permissions.get('public'),
                'authorized_ids': permissions.get('authorized_ids'),
            },
            'metadata': metadata
        }

        with get_orchestrator_client(channel_name) as client:
            return client.register_algo(args)

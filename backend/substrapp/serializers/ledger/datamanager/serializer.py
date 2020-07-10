from rest_framework import serializers

from django.conf import settings
from rest_framework.fields import CharField, DictField
from rest_framework.reverse import reverse

from substrapp import ledger
from substrapp.utils import get_hash
from substrapp.serializers.ledger.utils import PermissionsSerializer


class LedgerDataManagerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=30)
    objective_key = serializers.CharField(max_length=256, allow_blank=True, required=False, allow_null=True)
    permissions = PermissionsSerializer()
    metadata = DictField(child=CharField(), required=False, allow_null=True)

    def create(self, channel, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        data_type = validated_data.get('type')
        permissions = validated_data.get('permissions')
        objective_key = validated_data.get('objective_key', '')
        metadata = validated_data.get('metadata')

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        current_site = getattr(settings, "DEFAULT_DOMAIN")

        args = {
            'name': name,
            'openerHash': get_hash(instance.data_opener),
            'openerStorageAddress': current_site + reverse('substrapp:data_manager-opener', args=[instance.pk]),
            'type': data_type,
            'descriptionHash': get_hash(instance.description),
            'descriptionStorageAddress': current_site + reverse('substrapp:data_manager-description',
                                                                args=[instance.pk]),
            'objectiveKey': objective_key,
            'permissions': {'process': {
                'public': permissions.get('public'),
                'authorizedIDs': permissions.get('authorized_ids'),
            }},
            'metadata': metadata
        }
        return ledger.create_datamanager(channel, args, instance.pkhash)

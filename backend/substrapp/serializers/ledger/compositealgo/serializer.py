from rest_framework import serializers

from django.conf import settings
from rest_framework.fields import CharField, DictField
from rest_framework.reverse import reverse

from substrapp import ledger
from substrapp.utils import get_hash
from substrapp.serializers.ledger.utils import PermissionsSerializer


class LedgerCompositeAlgoSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=100)
    permissions = PermissionsSerializer()
    metadata = DictField(child=CharField(), required=False, allow_null=True)

    def create(self, channel_name, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        permissions = validated_data.get('permissions')
        metadata = validated_data.get('metadata')

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        current_site = getattr(settings, "DEFAULT_DOMAIN")

        args = {
            'key': instance.key,
            'name': name,
            'checksum': get_hash(instance.file),
            'storage_address': current_site + reverse('substrapp:composite_algo-file', args=[instance.key]),
            'description_checksum': get_hash(instance.description),
            'description_storage_address': current_site + reverse(
                'substrapp:composite_algo-description', args=[instance.key]),
            'permissions': {'process': {
                'public': permissions.get('public'),
                'authorized_ids': permissions.get('authorized_ids'),
            }},
            'metadata': metadata
        }
        return ledger.assets.create_compositealgo(channel_name, args, instance.key)

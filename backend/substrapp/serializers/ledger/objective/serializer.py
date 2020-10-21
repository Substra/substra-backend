from rest_framework import serializers
# from django.contrib.sites.models import Site
from django.conf import settings
from rest_framework.fields import CharField, DictField
from rest_framework.reverse import reverse

from substrapp import ledger
from substrapp.utils import get_hash
from substrapp.serializers.ledger.utils import PermissionsSerializer


class LedgerObjectiveSerializer(serializers.Serializer):
    test_data_sample_keys = serializers.ListField(child=serializers.UUIDField(), min_length=0, required=False)
    name = serializers.CharField(min_length=1, max_length=100)
    test_data_manager_key = serializers.UUIDField(required=False, allow_null=True)
    permissions = PermissionsSerializer()
    metrics_name = serializers.CharField(min_length=1, max_length=100)
    metadata = DictField(child=CharField(), required=False, allow_null=True)

    def create(self, channel_name, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        metrics_name = validated_data.get('metrics_name')
        permissions = validated_data.get('permissions')
        test_data_manager_key = validated_data.get('test_data_manager_key', None)
        test_data_sample_keys = validated_data.get('test_data_sample_keys', [])
        metadata = validated_data.get('metadata')

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        current_site = getattr(settings, "DEFAULT_DOMAIN")

        args = {
            'key': str(instance.pk),
            'name': name,
            'description_hash': get_hash(instance.description),
            'description_storage_address': current_site + reverse('substrapp:objective-description', args=[instance.pk]),  # noqa
            'metrics_name': metrics_name,
            'metrics_hash': get_hash(instance.metrics),
            'metrics_storage_address': current_site + reverse('substrapp:objective-metrics', args=[instance.pk]),
            'test_dataset': {
                'data_manager_key': str(test_data_manager_key) if test_data_manager_key else None,
                'data_sample_keys': [str(key) for key in test_data_sample_keys],
            },
            'permissions': {'process': {
                'public': permissions.get('public'),
                'authorized_ids': permissions.get('authorized_ids'),
            }},
            'metadata': metadata
        }
        return ledger.assets.create_objective(channel_name, args, instance.pkhash)

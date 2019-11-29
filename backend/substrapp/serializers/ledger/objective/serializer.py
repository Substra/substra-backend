from rest_framework import serializers
# from django.contrib.sites.models import Site
from django.conf import settings
from rest_framework.reverse import reverse

from substrapp.utils import get_hash
from substrapp.serializers.ledger.utils import PermissionsSerializer
from .util import createLedgerObjective
from .tasks import createLedgerObjectiveAsync


class LedgerObjectiveSerializer(serializers.Serializer):
    test_data_sample_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                                  min_length=0,
                                                  required=False)
    name = serializers.CharField(min_length=1, max_length=100)
    test_data_manager_key = serializers.CharField(max_length=256, allow_blank=True, required=False)
    permissions = PermissionsSerializer()
    metrics_name = serializers.CharField(min_length=1, max_length=100)

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        metrics_name = validated_data.get('metrics_name')
        permissions = validated_data.get('permissions')
        test_data_manager_key = validated_data.get('test_data_manager_key', '')
        test_data_sample_keys = validated_data.get('test_data_sample_keys', [])

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        current_site = getattr(settings, "DEFAULT_DOMAIN")

        args = {
            'name': name,
            'descriptionHash': get_hash(instance.description),
            'descriptionStorageAddress': current_site + reverse('substrapp:objective-description', args=[instance.pk]),  # noqa
            'metricsName': metrics_name,
            'metricsHash': get_hash(instance.metrics),
            'metricsStorageAddress': current_site + reverse('substrapp:objective-metrics', args=[instance.pk]),
            'testDataset': {
                'dataManagerKey': test_data_manager_key,
                'dataSampleKeys': test_data_sample_keys,
            },
            'permissions': {'process': {
                'public': permissions.get('public'),
                'authorizedIDs': permissions.get('authorized_ids'),
            }}
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            data = createLedgerObjective(args, instance.pkhash, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerObjectiveAsync.delay(args, instance.pkhash)
            data = {
                'message': 'Objective added in local db waiting for validation. '
                           'The substra network has been notified for adding this Objective'
            }

        return data

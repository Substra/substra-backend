from rest_framework import serializers, status
# from django.contrib.sites.models import Site
from django.conf import settings

from substrapp.models.utils import compute_hash
from .util import createLedgerChallenge
from .tasks import createLedgerChallengeAsync


class LedgerChallengeSerializer(serializers.Serializer):
    test_data_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                           min_length=1,
                                           max_length=None)
    name = serializers.CharField(min_length=1, max_length=60)
    permissions = serializers.CharField(min_length=1, max_length=60)
    metrics_name = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        metrics_name = validated_data.get('metrics_name')
        permissions = validated_data.get('permissions')
        test_data_keys = validated_data.get('test_data_keys')

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        # current_site = Site.objects.get_current()
        request = self.context.get('request', None)
        protocol = 'https://' if request.is_secure() else 'http://'
        host = '' if request is None else request.get_host()

        args = '"%(name)s", "%(descriptionHash)s", "%(descriptionStorageAddress)s", "%(metricsName)s", "%(metricsHash)s", "%(metricsStorageAddress)s", "%(testDataKeys)s", "%(permissions)s"' % {
            'name': name,
            'descriptionHash': compute_hash(instance.description.path),
            'descriptionStorageAddress': protocol + host + instance.description.url,
            'metricsName': metrics_name,
            'metricsHash': compute_hash(instance.metrics.path),
            'metricsStorageAddress': protocol + host + instance.metrics.url,
            'testDataKeys': ','.join([x for x in test_data_keys]),
            'permissions': permissions
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            data, st = createLedgerChallenge(args, instance.pkhash, sync=True)

            return data, st

        else:
            # use a celery task, as we are in an http request transaction
            createLedgerChallengeAsync.delay(args, instance.pkhash)
            st = status.HTTP_201_CREATED
            return {
                'message': 'Challenge added in local db waiting for validation. The susbtra network has been notified for adding this Challenge'}, st

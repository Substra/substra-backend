from rest_framework import serializers
# from django.contrib.sites.models import Site

from substrapp.models.utils import compute_hash
from .tasks import createLedgerChallenge


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

        # use a celery task, as we are in an http request transaction
        createLedgerChallenge.delay(args, instance.pkhash)

        return {
            'message': 'Challenge added in local db waiting for validation. The susbtra network has been notified for adding this Challenge'}

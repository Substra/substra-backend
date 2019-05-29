import json

from rest_framework import serializers, status

from django.conf import settings

from .util import createLedgerDataSample
from .tasks import createLedgerDataSampleAsync


class LedgerDataSampleSerializer(serializers.Serializer):
    data_manager_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                              min_length=1)
    test_only = serializers.BooleanField()

    def create(self, validated_data):
        instances = self.initial_data.get('instances')
        data_manager_keys = validated_data.get('data_manager_keys')
        test_only = validated_data.get('test_only')

        # Json
        # args = {
        #     'hashes': ','.join([x.pk for x in instances]),
        #     'dataManagerKeys': ','.join([x for x in data_manager_keys]),
        #     'testOnly': json.dumps(test_only),
        # }

        args = [
            ','.join([x.pk for x in instances]),
            ','.join([x for x in data_manager_keys]),
            json.dumps(test_only),
        ]

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            return createLedgerDataSample(args, [x.pk for x in instances], sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerDataSampleAsync.delay(args, [x.pk for x in instances])
            data = {
                'message': 'Data samples added in local db waiting for validation. '
                           'The substra network has been notified for adding this Data'
            }
            return data, status.HTTP_202_ACCEPTED

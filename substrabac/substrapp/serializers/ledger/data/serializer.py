import json

from rest_framework import serializers, status

from django.conf import settings

from .util import createLedgerData
from .tasks import createLedgerDataAsync


class LedgerDataSerializer(serializers.Serializer):
    dataset_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                         min_length=1,
                                         max_length=None)
    test_only = serializers.BooleanField()

    def create(self, validated_data):
        instances = self.initial_data.get('instances')
        dataset_keys = validated_data.get('dataset_keys')
        test_only = validated_data.get('test_only')

        args = '"%(hashes)s", "%(datasetKeys)s", "%(testOnly)s"' % {
            'hashes': ','.join([x.pk for x in instances]),
            'datasetKeys': ','.join([x for x in dataset_keys]),
            'testOnly': json.dumps(test_only),
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            return createLedgerData(args, [x.pk for x in instances], sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerDataAsync.delay(args, [x.pk for x in instances])
            data = {
                'message': 'Data added in local db waiting for validation. The substra network has been notified for adding this Data'
            }
            st = status.HTTP_202_ACCEPTED
            return data, st

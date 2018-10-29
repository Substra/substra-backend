import json

from rest_framework import serializers, status

from django.conf import settings

from .util import createLedgerData
from .tasks import createLedgerDataAsync


class LedgerDataSerializer(serializers.Serializer):
    dataset_key = serializers.CharField(max_length=256)
    size = serializers.IntegerField(min_value=0)
    test_only = serializers.BooleanField()

    def create(self, validated_data):
        instances = self.initial_data.get('instances')
        dataset_key = validated_data.get('dataset_key')
        size = validated_data.get('size')
        test_only = validated_data.get('test_only')

        args = '"%(hashes)s", "%(datasetKey)s", "%(size)s", "%(testOnly)s"' % {
            'hashes': ','.join([x.pk for x in instances]),
            'datasetKey': dataset_key,
            'size': size,
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

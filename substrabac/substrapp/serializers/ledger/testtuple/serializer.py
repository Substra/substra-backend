from rest_framework import serializers, status

from django.conf import settings

from .util import createLedgerTesttuple
from .tasks import createLedgerTesttupleAsync


class LedgerTestTupleSerializer(serializers.Serializer):
    traintuple_key = serializers.CharField(min_length=64, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False)
    test_data_sample_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                                  min_length=0,
                                                  required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)

    def get_args(self, validated_data):
        traintuple_key = validated_data.get('traintuple_key')
        data_manager_key = validated_data.get('data_manager_key', '')
        test_data_sample_keys = validated_data.get('test_data_sample_keys', [])
        tag = validated_data.get('tag', '')

        # args = '"%(traintupleKey)s", "%(dataManagerKey)s", "%(dataSampleKeys)s", "%(tag)s"' % {
        #     'traintupleKey': traintuple_key,
        #     'dataManagerKey': data_manager_key,
        #     'dataSampleKeys': ','.join(test_data_sample_keys),
        #     'tag': tag
        # }

        args = [
            traintuple_key,
            data_manager_key,
            ','.join([x for x in test_data_sample_keys]),
            tag
        ]

        return args

    def create(self, validated_data):
        args = self.get_args(validated_data)

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            return createLedgerTesttuple(args, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerTesttupleAsync.delay(args)

            data = {
                'message': 'The substra network has been notified for adding this Testtuple. Please be aware you won\'t get return values from the ledger. You will need to check manually'
            }
            st = status.HTTP_202_ACCEPTED
            return data, st

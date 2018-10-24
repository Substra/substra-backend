from rest_framework import serializers, status

from django.conf import settings

from .util import createLedgerTraintuple
from .tasks import createLedgerTraintupleAsync


class LedgerTrainTupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    model_key = serializers.CharField(min_length=64, max_length=64, allow_null=True, allow_blank=True)
    train_data_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                            min_length=1,
                                            max_length=None)

    def create(self, validated_data):
        algo_key = validated_data.get('algo_key')
        model_key = validated_data.get('model_key')
        train_data_keys = validated_data.get('train_data_keys')

        args = '"%(algoKey)s", "%(modelKey)s", "%(trainDataKeys)s"' % {
            'algoKey': algo_key,
            'modelKey': model_key,
            'trainDataKeys': ','.join([x for x in train_data_keys]),
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            return createLedgerTraintuple(args, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerTraintupleAsync.delay(args)

            data = {
                'message': 'The susbtra network has been notified for adding this Traintuple. Please be aware you won\'t get return values from the ledger. You will need to check manually'
            }
            st = status.HTTP_200_OK
            return data, st

from rest_framework import serializers, status

from django.conf import settings

from .util import createLedgerTraintuple
from .tasks import createLedgerTraintupleAsync


class LedgerTrainTupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    dataset_key = serializers.CharField(min_length=64, max_length=64)
    rank = serializers.IntegerField(allow_null=True, required=False)
    FLtask_key = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False)
    input_models_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                              min_length=0,
                                              max_length=None)
    train_data_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                            min_length=1,
                                            max_length=None)

    def create(self, validated_data):
        algo_key = validated_data.get('algo_key')
        dataset_key = validated_data.get('dataset_key')
        rank = validated_data.get('rank', '')
        FLtask_key = validated_data.get('FLtask_key', '')
        train_data_keys = validated_data.get('train_data_keys')
        input_models_keys = validated_data.get('input_models_keys')

        args = '"%(algoKey)s", "%(inModels)s", "%(datasetKey)s", "%(dataKeys)s", "%(FLtask)s", "%(rank)s"' % {
            'algoKey': algo_key,
            'rank': rank,
            'FLtask': FLtask_key,
            'inModels': ','.join([x for x in input_models_keys]),
            'datasetKey': dataset_key,
            'dataKeys': ','.join([x for x in train_data_keys]),
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            return createLedgerTraintuple(args, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerTraintupleAsync.delay(args)

            data = {
                'message': 'The substra network has been notified for adding this Traintuple. Please be aware you won\'t get return values from the ledger. You will need to check manually'
            }
            st = status.HTTP_202_ACCEPTED
            return data, st

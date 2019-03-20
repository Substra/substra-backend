from rest_framework import serializers, status

from django.conf import settings

from .util import createLedgerTraintuple
from .tasks import createLedgerTraintupleAsync


class LedgerTrainTupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64)
    objective_key = serializers.CharField(min_length=64, max_length=64)
    rank = serializers.IntegerField(allow_null=True, required=False)
    FLtask_key = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False)
    in_models_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                           min_length=0,
                                           required=False)
    train_data_sample_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                                   min_length=1)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)

    def get_args(self, validated_data):
        algo_key = validated_data.get('algo_key')
        data_manager_key = validated_data.get('data_manager_key')
        objective_key = validated_data.get('objective_key')
        rank = validated_data.get('rank', '')
        rank = '' if rank is None else rank  # rank should be an integer or empty string, not None
        FLtask_key = validated_data.get('FLtask_key', '')
        train_data_sample_keys = validated_data.get('train_data_sample_keys', [])
        in_models_keys = validated_data.get('in_models_keys')
        tag = validated_data.get('tag', '')

        # args = '"%(algoKey)s", "%(associatedObjective)s", "%(inModels)s", "%(dataManagerKey)s", "%(dataSampleKeys)s", "%(FLtask)s", "%(rank)s", "%(tag)s"' % {
        #     'algoKey': algo_key,
        #     'associatedObjective': objective_key,
        #     'inModels': ','.join(in_models_keys),
        #     'dataManagerKey': data_manager_key,
        #     'dataSampleKeys': ','.join(train_data_sample_keys),
        #     'FLtask': FLtask_key,
        #     'rank': rank,
        #     'tag': tag
        # }

        args = [
            algo_key,
            objective_key,
            ','.join([x for x in in_models_keys]),
            data_manager_key,
            ','.join([x for x in train_data_sample_keys]),
            FLtask_key,
            rank,
            tag,
        ]

        return args

    def create(self, validated_data):
        args = self.get_args(validated_data)

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

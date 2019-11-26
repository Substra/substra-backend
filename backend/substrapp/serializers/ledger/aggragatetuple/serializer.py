from rest_framework import serializers

from django.conf import settings

from .util import createLedgerAggregateTuple
from .tasks import createLedgerAggregateTupleAsync


class LedgerAggregateTupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    objective_key = serializers.CharField(min_length=64, max_length=64)
    rank = serializers.IntegerField(allow_null=True, required=False, default=0)
    compute_plan_id = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False)
    in_models_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                           min_length=0,
                                           required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)

    def get_args(self, validated_data):
        algo_key = validated_data.get('algo_key')
        objective_key = validated_data.get('objective_key')
        rank = validated_data.get('rank', '')
        rank = '' if rank is None else str(rank)
        compute_plan_id = validated_data.get('compute_plan_id', '')
        in_models_keys = validated_data.get('in_models_keys', [])
        tag = validated_data.get('tag', '')

        args = {
            'algoKey': algo_key,
            'objectiveKey': objective_key,
            'inModels': in_models_keys,
            'computePlanID': compute_plan_id,
            'rank': rank,
            'tag': tag
        }

        return args

    def create(self, validated_data):
        args = self.get_args(validated_data)

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            data = createLedgerAggregateTuple(args, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerAggregateTupleAsync.delay(args)
            data = {
                'message': 'The substra network has been notified for adding this Aggregatetuple. '
                           'Please be aware you won\'t get return values from the ledger. '
                           'You will need to check manually'
            }

        return data

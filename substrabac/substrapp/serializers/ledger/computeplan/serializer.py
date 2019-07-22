from rest_framework import serializers

from django.conf import settings

from .util import createLedgerComputePlan
from .tasks import createLedgerComputePlanAsync


class ComputePlanTraintupleSerializer(serializers.Serializer):
    data_manager_key = serializers.CharField(min_length=64, max_length=64)
    train_data_sample_keys = serializers.ListField(
        child=serializers.CharField(min_length=64, max_length=64),
        min_length=1)
    traintuple_id = serializers.CharField(min_length=1, max_length=64)
    in_models_ids = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=64),
        min_length=0,
        required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)


class LedgerComputePlanSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    objective_key = serializers.CharField(min_length=64, max_length=64)
    traintuples = ComputePlanTraintupleSerializer(many=True)

    def get_args(self, validated_data):
        algo_key = validated_data.get('algo_key')
        objective_key = validated_data.get('objective_key')
        traintuples = []

        for traintuple in validated_data.get('traintuples', []):
            traintuples.append({
                'dataManagerKey': traintuple.get('data_manager_key'),
                'dataSampleKeys': traintuple.get('train_data_sample_keys', []),
                'id': traintuple.get('traintuple_id'),
                'inModelIds': traintuple.get('in_models_ids'),
                'tag': traintuple.get('tag'),
            })

        args = {
            'algoKey': algo_key,
            'objectiveKey': objective_key,
            'traintuples': traintuples,
        }

        return args

    def create(self, validated_data):
        args = self.get_args(validated_data)

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            data = createLedgerComputePlan(args, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerComputePlanAsync.delay(args)
            data = {
                'message': 'The substra network has been notified for adding this ComputePlan. '
                           'Please be aware you won\'t get return values from the ledger. '
                           'You will need to check manually'
            }

        return data

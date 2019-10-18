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


class ComputePlanTesttupleSerializer(serializers.Serializer):
    traintuple_id = serializers.CharField(min_length=1, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64, required=False)
    test_data_sample_keys = serializers.ListField(
        child=serializers.CharField(min_length=64, max_length=64),
        min_length=0,
        required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)


class LedgerComputePlanSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    objective_key = serializers.CharField(min_length=64, max_length=64)
    traintuples = ComputePlanTraintupleSerializer(many=True)
    testtuples = ComputePlanTesttupleSerializer(many=True)

    def get_args(self, data):
        # convert snake case fields to camel case fields to match chaincode expected inputs
        traintuples = []
        for data_traintuple in data['traintuples']:
            traintuple = {
                'dataManagerKey': data_traintuple['data_manager_key'],
                'dataSampleKeys': data_traintuple['train_data_sample_keys'],
                'id': data_traintuple['traintuple_id'],
            }
            if 'in_models_ids' in data_traintuple:
                traintuple['inModelsIDs'] = data_traintuple['in_models_ids']
            if 'tag' in data_traintuple:
                traintuple['tag'] = data_traintuple['tag']

            traintuples.append(traintuple)

        testtuples = []
        for data_testtuple in data['testtuples']:
            testtuple = {
                'traintupleID': data_testtuple['traintuple_id'],
            }
            if 'tag' in data_testtuple:
                testtuple['tag'] = data_testtuple['tag']
            if 'data_manager_key' in data_testtuple:
                testtuple['dataManagerKey'] = data_testtuple['data_manager_key']
            if 'test_data_sample_keys' in data_testtuple:
                testtuple['dataSampleKeys'] = data_testtuple['test_data_sample_keys']

            testtuples.append(testtuple)

        return {
            'algoKey': data['algo_key'],
            'objectiveKey': data['objective_key'],
            'traintuples': traintuples,
            'testtuples': testtuples,
        }

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

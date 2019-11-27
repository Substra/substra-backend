from rest_framework import serializers

from django.conf import settings

from .util import createLedgerComputePlan
from .tasks import createLedgerComputePlanAsync

from substrapp.serializers.ledger.utils import PermissionsSerializer


class ComputePlanTraintupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
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
    algo_key = serializers.CharField(min_length=64, max_length=64)
    traintuple_id = serializers.CharField(min_length=1, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64, required=False)
    test_data_sample_keys = serializers.ListField(
        child=serializers.CharField(min_length=64, max_length=64),
        min_length=0,
        required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)


class ComputePlanCompositeTrainTupleSerializer(ComputePlanTraintupleSerializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64)
    train_data_sample_keys = serializers.ListField(
        child=serializers.CharField(min_length=64, max_length=64),
        min_length=1)
    in_head_model_id = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False)
    in_trunk_model_id = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False)
    out_trunk_model_permissions = PermissionsSerializer()
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)


class ComputePlanAggregatetupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    worker = serializers.CharField()
    in_models_ids = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=64),
        min_length=0,
        required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)


class LedgerComputePlanSerializer(serializers.Serializer):
    objective_key = serializers.CharField(min_length=64, max_length=64)
    traintuples = ComputePlanTraintupleSerializer(many=True)
    testtuples = ComputePlanTesttupleSerializer(many=True)
    composite_traintuples = ComputePlanCompositeTrainTupleSerializer(many=True)
    aggregatetuples = ComputePlanAggregatetupleSerializer(many=True)

    def get_args(self, data):
        # convert snake case fields to camel case fields to match chaincode expected inputs
        traintuples = []
        for data_traintuple in data['traintuples']:
            traintuple = {
                'dataManagerKey': data_traintuple['data_manager_key'],
                'dataSampleKeys': data_traintuple['train_data_sample_keys'],
                'algoKey': data_traintuple['algo_key'],
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
                'algoKey': data_traintuple['algo_key'],
                'traintupleID': data_testtuple['traintuple_id'],
            }
            if 'tag' in data_testtuple:
                testtuple['tag'] = data_testtuple['tag']
            if 'data_manager_key' in data_testtuple:
                testtuple['dataManagerKey'] = data_testtuple['data_manager_key']
            if 'test_data_sample_keys' in data_testtuple:
                testtuple['dataSampleKeys'] = data_testtuple['test_data_sample_keys']

            testtuples.append(testtuple)

        composite_traintuples = []
        for data_composite_traintuple in data['composite_traintuples']:
            composite_traintuple = {
                'algoKey': data_composite_traintuple['algo_key'],
                'dataManagerKey': data_composite_traintuple['data_manager_key'],
                'dataSampleKeys': data_composite_traintuple['train_data_sample_keys'],
            }

            if 'tag' in data_composite_traintuple:
                composite_traintuple['tag'] = data_composite_traintuple['tag']
            if 'in_head_model_id' in data_composite_traintuple:
                composite_traintuple['inHeadModelID'] = data_composite_traintuple['in_head_model_id']
            if 'in_trunk_model_id' in data_composite_traintuple:
                composite_traintuple['inTrunkModelID'] = data_composite_traintuple['in_trunk_model_id']
            if 'out_trunk_model_permissions' in data_composite_traintuple:
                composite_traintuple['outTrunkModelPermissions'] = data_composite_traintuple[
                    'out_trunk_model_permissions'
                ]

            composite_traintuples.append(composite_traintuple)

        aggregatetuples = []
        for data_aggregatetuple in data['aggregatetuples']:
            aggregatetuple = {
                'algoKey': data_aggregatetuple['algo_key'],
                'worker': data_aggregatetuple['worker'],
            }

            if 'in_models_ids' in data_aggregatetuple:
                aggregatetuple['inModelsIDs'] = data_aggregatetuple['in_models_ids']
            if 'tag' in data_aggregatetuple:
                aggregatetuple['tag'] = data_aggregatetuple['tag']

            aggregatetuples.append(aggregatetuple)

        return {
            'objectiveKey': data['objective_key'],
            'traintuples': traintuples,
            'testtuples': testtuples,
            'composite_traintuples': composite_traintuples,
            'aggregatetuples': aggregatetuples
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

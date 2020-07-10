from rest_framework import serializers
from rest_framework.fields import DictField, CharField

from substrapp import ledger
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
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False, allow_null=True)
    metadata = DictField(child=CharField(), required=False, allow_null=True)


class ComputePlanTesttupleSerializer(serializers.Serializer):
    traintuple_id = serializers.CharField(min_length=1, max_length=64)
    objective_key = serializers.CharField(min_length=64, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64, required=False)
    test_data_sample_keys = serializers.ListField(
        child=serializers.CharField(min_length=64, max_length=64),
        min_length=0,
        required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False, allow_null=True)
    metadata = DictField(child=CharField(), required=False, allow_null=True)


class ComputePlanCompositeTrainTupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64)
    train_data_sample_keys = serializers.ListField(
        child=serializers.CharField(min_length=64, max_length=64),
        min_length=1)
    composite_traintuple_id = serializers.CharField(min_length=1, max_length=64)
    in_head_model_id = serializers.CharField(min_length=1, max_length=64, allow_blank=True, required=False,
                                             allow_null=True)
    in_trunk_model_id = serializers.CharField(min_length=1, max_length=64, allow_blank=True, required=False,
                                              allow_null=True)
    out_trunk_model_permissions = PermissionsSerializer()
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False, allow_null=True)
    metadata = DictField(child=CharField(), required=False, allow_null=True)


class ComputePlanAggregatetupleSerializer(serializers.Serializer):
    aggregatetuple_id = serializers.CharField(min_length=1, max_length=64)
    algo_key = serializers.CharField(min_length=64, max_length=64)
    worker = serializers.CharField()
    in_models_ids = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=64),
        min_length=0,
        required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False, allow_null=True)
    metadata = DictField(child=CharField(), required=False, allow_null=True)


class LedgerComputePlanSerializer(serializers.Serializer):
    traintuples = ComputePlanTraintupleSerializer(many=True, required=False)
    testtuples = ComputePlanTesttupleSerializer(many=True, required=False)
    composite_traintuples = ComputePlanCompositeTrainTupleSerializer(many=True, required=False)
    aggregatetuples = ComputePlanAggregatetupleSerializer(many=True, required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False, allow_null=True)
    metadata = DictField(child=CharField(), required=False, allow_null=True)
    clean_models = serializers.BooleanField(required=False)

    def get_args(self, data):
        # convert snake case fields to camel case fields to match chaincode expected inputs
        traintuples = []
        for data_traintuple in data.get('traintuples', []):
            traintuple = {
                'dataManagerKey': data_traintuple['data_manager_key'],
                'dataSampleKeys': data_traintuple['train_data_sample_keys'],
                'algoKey': data_traintuple['algo_key'],
                'id': data_traintuple['traintuple_id'],
                'metadata': data_traintuple.get('metadata'),
            }
            if 'in_models_ids' in data_traintuple:
                traintuple['inModelsIDs'] = data_traintuple['in_models_ids']
            if 'tag' in data_traintuple:
                traintuple['tag'] = data_traintuple['tag']

            traintuples.append(traintuple)

        testtuples = []
        for data_testtuple in data.get('testtuples', []):
            testtuple = {
                'traintupleID': data_testtuple['traintuple_id'],
                'objectiveKey': data_testtuple['objective_key'],
                'metadata': data_testtuple.get('metadata'),
            }
            if 'tag' in data_testtuple:
                testtuple['tag'] = data_testtuple['tag']
            if 'data_manager_key' in data_testtuple:
                testtuple['dataManagerKey'] = data_testtuple['data_manager_key']
            if 'test_data_sample_keys' in data_testtuple:
                testtuple['dataSampleKeys'] = data_testtuple['test_data_sample_keys']

            testtuples.append(testtuple)

        composite_traintuples = []
        for data_composite_traintuple in data.get('composite_traintuples', []):
            composite_traintuple = {
                'algoKey': data_composite_traintuple['algo_key'],
                'dataManagerKey': data_composite_traintuple['data_manager_key'],
                'dataSampleKeys': data_composite_traintuple['train_data_sample_keys'],
                'id': data_composite_traintuple['composite_traintuple_id'],
                'metadata': data_composite_traintuple.get('metadata'),
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
        for data_aggregatetuple in data.get('aggregatetuples', []):
            aggregatetuple = {
                'algoKey': data_aggregatetuple['algo_key'],
                'worker': data_aggregatetuple['worker'],
                'id': data_aggregatetuple['aggregatetuple_id'],
                'metadata': data_aggregatetuple.get('metadata'),
            }

            if 'in_models_ids' in data_aggregatetuple:
                aggregatetuple['inModelsIDs'] = data_aggregatetuple['in_models_ids']
            if 'tag' in data_aggregatetuple:
                aggregatetuple['tag'] = data_aggregatetuple['tag']

            aggregatetuples.append(aggregatetuple)

        return {
            'traintuples': traintuples,
            'testtuples': testtuples,
            'compositeTraintuples': composite_traintuples,
            'aggregatetuples': aggregatetuples,
            'metadata': data.get('metadata'),
            'tag': data.get('tag'),
            'cleanModels': data.get('clean_models', False),
        }

    def create(self, channel, validated_data):
        args = self.get_args(validated_data)
        return ledger.create_computeplan(channel, args)

    def update(self, channel, compute_plan_id, validated_data):
        args = self.get_args(validated_data)
        del args['tag']
        args['computePlanID'] = compute_plan_id
        return ledger.update_computeplan(channel, args)

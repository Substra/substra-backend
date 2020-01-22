from rest_framework import serializers

from substrapp import ledger
from substrapp.serializers.ledger.utils import PermissionsSerializer


class AddComputePlanTraintupleSerializer(serializers.Serializer):
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


class UpdateComputePlanTraintupleSerializer(AddComputePlanTraintupleSerializer):
    in_models_keys = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=64),
        min_length=0,
        required=False)


class AddComputePlanTesttupleSerializer(serializers.Serializer):
    traintuple_id = serializers.CharField(min_length=1, max_length=64)
    objective_key = serializers.CharField(min_length=64, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64, required=False)
    test_data_sample_keys = serializers.ListField(
        child=serializers.CharField(min_length=64, max_length=64),
        min_length=0,
        required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)


class UpdateComputePlanTesttupleSerializer(AddComputePlanTesttupleSerializer):
    traintuple_id = serializers.CharField(min_length=1, max_length=64, required=False)
    traintuple_key = serializers.CharField(min_length=1, max_length=64, required=False)

    def validate(self, data):
        data = super().validate(data)

        if not data['traintuple_key'] and not data['traintuple_id']:
            raise serializers.ValidationError('Missing value: one of traintuple_key and traintuple_id must be filled')

        if data['traintuple_key'] and data['traintuple_id']:
            raise serializers.ValidationError('Fields traintuple_key and traintuple_id are mutually exclusive')

        return data


class AddComputePlanCompositeTrainTupleSerializer(serializers.Serializer):
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
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)


class UpdateComputePlanCompositeTrainTupleSerializer(AddComputePlanCompositeTrainTupleSerializer):
    in_head_model_key = serializers.CharField(min_length=1, max_length=64, allow_blank=True, required=False,
                                              allow_null=True)
    in_trunk_model_key = serializers.CharField(min_length=1, max_length=64, allow_blank=True, required=False,
                                               allow_null=True)

    def validate(self, data):
        super().validate(data)

        if data['in_head_model_key'] and data['in_head_model_id']:
            raise serializers.ValidationError('Fields in_head_model_key and in_head_model_id are mutually exclusive')

        if data['in_trunk_model_key'] and data['in_trunk_model_id']:
            raise serializers.ValidationError('Fields in_trunk_model_key and in_trunk_model_id are mutually exclusive')


class AddComputePlanAggregatetupleSerializer(serializers.Serializer):
    aggregatetuple_id = serializers.CharField(min_length=1, max_length=64)
    algo_key = serializers.CharField(min_length=64, max_length=64)
    worker = serializers.CharField()
    in_models_ids = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=64),
        min_length=0,
        required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)


class UpdateComputePlanAggregatetupleSerializer(AddComputePlanAggregatetupleSerializer):
    in_models_keys = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=64),
        min_length=0,
        required=False)


class LedgerAddComputePlanSerializer(serializers.Serializer):
    traintuples = AddComputePlanTraintupleSerializer(many=True, required=False)
    testtuples = AddComputePlanTesttupleSerializer(many=True, required=False)
    composite_traintuples = AddComputePlanCompositeTrainTupleSerializer(many=True, required=False)
    aggregatetuples = AddComputePlanAggregatetupleSerializer(many=True, required=False)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)

    def get_args(self, data):
        # convert snake case fields to camel case fields to match chaincode expected inputs
        traintuples = []
        for data_traintuple in data.get('traintuples', []):
            traintuple = {
                'dataManagerKey': data_traintuple['data_manager_key'],
                'dataSampleKeys': data_traintuple['train_data_sample_keys'],
                'algoKey': data_traintuple['algo_key'],
                'id': data_traintuple['traintuple_id'],
            }
            if 'in_models_ids' in data_traintuple:
                traintuple['inModelsIDs'] = data_traintuple['in_models_ids']
            if 'in_models_keys' in data_traintuple:
                traintuple['inModelsIDs'] = data_traintuple['in_models_ids']
            if 'tag' in data_traintuple:
                traintuple['tag'] = data_traintuple['tag']

            traintuples.append(traintuple)

        testtuples = []
        for data_testtuple in data.get('testtuples', []):
            testtuple = {
                'objectiveKey': data_testtuple['objective_key'],
            }
            if 'traintuple_id' in data_testtuple:
                testtuple['traintupleID'] = data_testtuple['traintuple_id']
            if 'traintuple_key' in data_testtuple:
                testtuple['traintupleKey'] = data_testtuple['traintuple_key']
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
            }

            if 'tag' in data_composite_traintuple:
                composite_traintuple['tag'] = data_composite_traintuple['tag']
            if 'in_head_model_id' in data_composite_traintuple:
                composite_traintuple['inHeadModelID'] = data_composite_traintuple['in_head_model_id']
            if 'in_head_model_key' in data_composite_traintuple:
                composite_traintuple['inHeadModelKey'] = data_composite_traintuple['in_head_model_key']
            if 'in_trunk_model_id' in data_composite_traintuple:
                composite_traintuple['inTrunkModelID'] = data_composite_traintuple['in_trunk_model_id']
            if 'in_trunk_model_key' in data_composite_traintuple:
                composite_traintuple['inTrunkModelKey'] = data_composite_traintuple['in_trunk_model_key']
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
            }

            if 'in_models_ids' in data_aggregatetuple:
                aggregatetuple['inModelsIDs'] = data_aggregatetuple['in_models_ids']
            if 'in_models_keys' in data_aggregatetuple:
                aggregatetuple['inModelsKeys'] = data_aggregatetuple['in_models_keys']
            if 'tag' in data_aggregatetuple:
                aggregatetuple['tag'] = data_aggregatetuple['tag']

            aggregatetuples.append(aggregatetuple)

        return {
            'traintuples': traintuples,
            'testtuples': testtuples,
            'compositeTraintuples': composite_traintuples,
            'aggregatetuples': aggregatetuples,
            'tag': data.get('tag'),
        }

    def create(self, validated_data):
        args = self.get_args(validated_data)
        return ledger.create_computeplan(args)


class LedgerUpdateComputePlanSerializer(LedgerAddComputePlanSerializer):
    compute_plan_id = serializers.CharField(min_length=1, max_length=64)

    traintuples = UpdateComputePlanTraintupleSerializer(many=True, required=False)
    testtuples = UpdateComputePlanTesttupleSerializer(many=True, required=False)
    composite_traintuples = UpdateComputePlanCompositeTrainTupleSerializer(many=True, required=False)
    aggregatetuples = UpdateComputePlanAggregatetupleSerializer(many=True, required=False)

    tag = None

    def get_args(self, data):
        args = super().get_args(data)
        args['computePlanID'] = args['compute_plan_id']
        return args

    def update(self, instance, validated_data):
        args = self.get_args(validated_data)
        return ledger.update_compute_plan(args)

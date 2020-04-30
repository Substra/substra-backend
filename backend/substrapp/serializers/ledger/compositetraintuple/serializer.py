from rest_framework import serializers

from substrapp import ledger
from substrapp.serializers.ledger.utils import PermissionsSerializer


class LedgerCompositeTraintupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64)
    rank = serializers.IntegerField(allow_null=True, required=False, default=0)
    compute_plan_id = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False,
                                            allow_null=True)
    in_head_model_key = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False,
                                              allow_null=True)
    in_trunk_model_key = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False,
                                               allow_null=True)
    out_trunk_model_permissions = PermissionsSerializer()
    train_data_sample_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                                   min_length=1)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False, allow_null=True)

    def get_args(self, validated_data):
        algo_key = validated_data.get('algo_key')
        data_manager_key = validated_data.get('data_manager_key')
        rank = validated_data.get('rank', '')
        rank = '' if rank is None else str(rank)
        compute_plan_id = validated_data.get('compute_plan_id', '')
        train_data_sample_keys = validated_data.get('train_data_sample_keys', [])
        in_head_model_key = validated_data.get('in_head_model_key')
        in_trunk_model_key = validated_data.get('in_trunk_model_key')
        out_trunk_model_permissions = validated_data.get('out_trunk_model_permissions')
        tag = validated_data.get('tag', '')

        args = {
            'algoKey': algo_key,
            'inHeadModelKey': in_head_model_key,
            'inTrunkModelKey': in_trunk_model_key,
            'outTrunkModelPermissions': {'process': {
                'public': out_trunk_model_permissions.get('public'),
                'authorizedIDs': out_trunk_model_permissions.get('authorized_ids'),
            }},
            'dataManagerKey': data_manager_key,
            'dataSampleKeys': train_data_sample_keys,
            'computePlanID': compute_plan_id,
            'rank': rank,
            'tag': tag
        }

        return args

    def create(self, validated_data):
        args = self.get_args(validated_data)
        return ledger.create_compositetraintuple(args)

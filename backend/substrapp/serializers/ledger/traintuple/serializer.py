from rest_framework import serializers
from rest_framework.fields import CharField, DictField

from substrapp import ledger


class LedgerTrainTupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64)
    rank = serializers.IntegerField(allow_null=True, required=False, default=0)
    compute_plan_id = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False,
                                            allow_null=True)
    in_models_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                           min_length=0,
                                           required=False, allow_null=True)
    train_data_sample_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                                   min_length=1)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False, allow_null=True)
    metadata = DictField(child=CharField(), required=False, allow_null=True)

    def get_args(self, validated_data):
        algo_key = validated_data.get('algo_key')
        data_manager_key = validated_data.get('data_manager_key')
        rank = validated_data.get('rank', '')
        rank = '' if rank is None else str(rank)
        compute_plan_id = validated_data.get('compute_plan_id', '')
        train_data_sample_keys = validated_data.get('train_data_sample_keys', [])
        in_models_keys = validated_data.get('in_models_keys', [])
        tag = validated_data.get('tag', '')
        metadata = validated_data.get('metadata')

        args = {
            'algoKey': algo_key,
            'inModels': in_models_keys,
            'dataManagerKey': data_manager_key,
            'dataSampleKeys': train_data_sample_keys,
            'computePlanID': compute_plan_id,
            'rank': rank,
            'tag': tag,
            'metadata': metadata
        }

        return args

    def create(self, channel, validated_data):
        args = self.get_args(validated_data)
        return ledger.create_traintuple(channel, args)

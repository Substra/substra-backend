from rest_framework import serializers
from rest_framework.fields import CharField, DictField

from substrapp.ledger import assets


class LedgerTrainTupleSerializer(serializers.Serializer):
    key = serializers.UUIDField()
    algo_key = serializers.UUIDField()
    data_manager_key = serializers.UUIDField()
    rank = serializers.IntegerField(allow_null=True, required=False, default=0)
    compute_plan_id = serializers.UUIDField(required=False, allow_null=True)
    in_models_keys = serializers.ListField(child=serializers.UUIDField(),
                                           min_length=0,
                                           required=False, allow_null=True)
    train_data_sample_keys = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False, allow_null=True)
    metadata = DictField(child=CharField(), required=False, allow_null=True)

    def get_args(self, validated_data):
        key = validated_data.get('key')
        algo_key = validated_data.get('algo_key')
        data_manager_key = validated_data.get('data_manager_key')
        rank = validated_data.get('rank', '')
        rank = '' if rank is None else str(rank)
        compute_plan_id = validated_data.get('compute_plan_id', None)
        train_data_sample_keys = validated_data.get('train_data_sample_keys', [])
        in_models_keys = [str(key) for key in validated_data.get('in_models_keys', [])]
        tag = validated_data.get('tag', '')
        metadata = validated_data.get('metadata')

        args = {
            'key': str(key),
            'algo_key': str(algo_key),
            'in_models': in_models_keys,
            'data_manager_key': str(data_manager_key),
            'data_sample_keys': [str(key) for key in train_data_sample_keys],
            'compute_plan_id': str(compute_plan_id) if compute_plan_id else None,
            'rank': rank,
            'tag': tag,
            'metadata': metadata
        }

        return args

    def create(self, channel_name, validated_data):
        args = self.get_args(validated_data)
        return assets.create_traintuple(channel_name, args)

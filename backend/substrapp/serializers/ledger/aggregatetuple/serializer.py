from rest_framework import serializers
from rest_framework.fields import CharField, DictField

from substrapp import ledger


class LedgerAggregateTupleSerializer(serializers.Serializer):
    key = serializers.UUIDField()
    algo_key = serializers.UUIDField()
    rank = serializers.IntegerField(allow_null=True, required=False, default=0)
    worker = serializers.CharField()
    compute_plan_key = serializers.UUIDField(required=False, allow_null=True)
    in_models_keys = serializers.ListField(child=serializers.UUIDField(),
                                           min_length=0,
                                           required=False, allow_null=True)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False, allow_null=True)
    metadata = DictField(child=CharField(), required=False, allow_null=True)

    def get_args(self, validated_data):
        key = validated_data.get('key')
        algo_key = validated_data.get('algo_key')
        rank = validated_data.get('rank', '')
        rank = '' if rank is None else str(rank)
        worker = validated_data.get('worker')
        compute_plan_key = validated_data.get('compute_plan_key')
        in_models_keys = validated_data.get('in_models_keys', [])
        tag = validated_data.get('tag', '')
        metadata = validated_data.get('metadata')

        args = {
            'key': key,
            'algo_key': algo_key,
            'in_models': in_models_keys,
            'compute_plan_key': compute_plan_key,
            'rank': rank,
            'worker': worker,
            'tag': tag,
            'metadata': metadata
        }

        return args

    def create(self, channel_name, validated_data):
        args = self.get_args(validated_data)
        return ledger.assets.create_aggregatetuple(channel_name, args)

from rest_framework import serializers
from rest_framework.fields import CharField, DictField

from substrapp import ledger


class LedgerTestTupleSerializer(serializers.Serializer):
    traintuple_key = serializers.CharField(min_length=64, max_length=64)
    objective_key = serializers.CharField(min_length=64, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False,
                                             allow_null=True)
    test_data_sample_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                                  min_length=0,
                                                  required=False, allow_null=True)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False, allow_null=True)
    metadata = DictField(child=CharField(), required=False, allow_null=True)

    def get_args(self, validated_data):
        traintuple_key = validated_data.get('traintuple_key')
        objective_key = validated_data.get('objective_key')
        data_manager_key = validated_data.get('data_manager_key', '')
        test_data_sample_keys = validated_data.get('test_data_sample_keys', [])
        tag = validated_data.get('tag', '')
        metadata = validated_data.get('metadata')

        args = {
            'traintupleKey': traintuple_key,
            'objectiveKey': objective_key,
            'dataManagerKey': data_manager_key,
            'dataSampleKeys': test_data_sample_keys,
            'tag': tag,
            'metadata': metadata
        }

        return args

    def create(self, channel, validated_data):
        args = self.get_args(validated_data)
        return ledger.create_testtuple(channel, args)

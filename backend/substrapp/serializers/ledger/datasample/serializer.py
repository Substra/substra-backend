import json

from rest_framework import serializers

from substrapp import ledger


class LedgerDataSampleSerializer(serializers.Serializer):
    data_manager_keys = serializers.ListField(child=serializers.UUIDField())
    test_only = serializers.BooleanField()

    def create(self, channel_name, validated_data):
        instances = self.initial_data.get('instances')
        data_manager_keys = validated_data.get('data_manager_keys')
        test_only = validated_data.get('test_only')

        args = {
            'keys': [x.pk for x in instances],
            'data_manager_keys': data_manager_keys,
            'testOnly': json.dumps(test_only),
        }
        return ledger.assets.create_datasamples(channel_name, args, [x.pk for x in instances])


class LedgerDataSampleUpdateSerializer(serializers.Serializer):
    data_manager_keys = serializers.ListField(child=serializers.UUIDField())
    data_sample_keys = serializers.ListField(child=serializers.UUIDField(), min_length=1)

    def create(self, channel_name, validated_data):
        args = {
            'keys': validated_data.get('data_sample_keys'),
            'data_manager_keys': validated_data.get('data_manager_keys'),
        }
        return ledger.assets.update_datasample(channel_name, args)

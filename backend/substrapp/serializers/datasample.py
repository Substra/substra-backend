
from rest_framework import serializers
from substrapp.models import DataSample

from substrapp.orchestrator import get_orchestrator_client


class DataSampleSerializer(serializers.ModelSerializer):
    # write_only because sensitive data should never be served by the API.
    file = serializers.FileField(write_only=True, required=False)
    # servermedias
    path = serializers.CharField(max_length=8192, required=False)

    class Meta:
        model = DataSample
        fields = '__all__'

    def validate(self, data):
        if bool(data.get("file")) == bool(data.get("path")):
            raise serializers.ValidationError("Expect either file or path.")
        return super().validate(data)


class OrchestratorDataSampleSerializer(serializers.Serializer):
    data_manager_keys = serializers.ListField(child=serializers.UUIDField())
    test_only = serializers.BooleanField()

    def create(self, channel_name, validated_data):
        instances = self.initial_data.get('instances')
        data_manager_keys = validated_data.get('data_manager_keys')
        test_only = validated_data.get('test_only')

        samples = [{
            'key': str(i.key),
            'data_manager_keys': [str(key) for key in data_manager_keys],
            'test_only': test_only,
            'checksum': i.checksum,
        } for i in instances]
        param = {
            'samples': samples,
        }
        with get_orchestrator_client(channel_name) as client:
            return client.register_datasamples(param)


class OrchestratorDataSampleUpdateSerializer(serializers.Serializer):
    data_manager_keys = serializers.ListField(child=serializers.UUIDField())
    data_sample_keys = serializers.ListField(child=serializers.UUIDField(), min_length=1)

    def create(self, channel_name, validated_data):
        args = {
            'keys': [str(key) for key in validated_data.get('data_sample_keys')],
            'data_manager_keys': [str(key) for key in validated_data.get('data_manager_keys')],
        }
        with get_orchestrator_client(channel_name) as client:
            return client.update_datasample(args)

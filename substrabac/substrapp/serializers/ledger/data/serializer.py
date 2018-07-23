from rest_framework import serializers

from .tasks import createLedgerData


class LedgerDataSerializer(serializers.Serializer):
    dataset_key = serializers.CharField(max_length=256)
    size = serializers.IntegerField(min_value=0)
    test_only = serializers.BooleanField()

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        dataset_key = validated_data.get('dataset_key')
        size = validated_data.get('size')
        test_only = validated_data.get('test_only')

        args = '"%(hashes)s", "%(datasetKey)s", "%(size)s", "%(testOnly)s""' % {
            'hashes': [instance.pkhash],
            'datasetKey': dataset_key,
            'size': size,
            'testOnly': test_only,
        }

        # use a celery task, as we are in an http request transaction
        createLedgerData.delay(args, instance.pkhash)

        return {
            'message': 'Data added in local db waiting for validation. The susbtra network has been notified for adding this Data'}

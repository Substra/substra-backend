from rest_framework import serializers

from .tasks import createLedgerTraintuple


class LedgerTrainTupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    model_key = serializers.CharField(min_length=64, max_length=64)
    train_data_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                            min_length=1,
                                            max_length=None)

    def create(self, validated_data):
        algo_key = validated_data.get('algo_key')
        model_key = validated_data.get('model_key')
        train_data_keys = validated_data.get('train_data_keys')

        args = '"%(algoKey)s", "%(modelKey)s", "%(trainDataKeys)s"' % {
            'algoKey': algo_key,
            'modelKey': model_key,
            'trainDataKeys': ','.join([x for x in train_data_keys]),
        }

        # use a celery task, as we are in an http request transaction
        createLedgerTraintuple.delay(args)

        return {
            'message': 'The susbtra network has been notified for adding this Traintuple. Please be aware you won\'t get return values from the ledger. You will need to check manually'}
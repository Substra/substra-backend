from rest_framework import serializers

from substrapp.conf import conf
from substrapp.utils import invokeLedger


class LedgerTrainTupleSerializer(serializers.Serializer):
    challenge_key = serializers.CharField(min_length=64, max_length=64)
    algo_key = serializers.CharField(min_length=64, max_length=64)
    model_key = serializers.CharField(min_length=64, max_length=64)
    train_data_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                            min_length=1,
                                            max_length=None)

    def create(self, validated_data):
        challenge_key = validated_data.get('challenge_key')
        algo_key = validated_data.get('algo_key')
        model_key = validated_data.get('model_key')
        train_data_keys = validated_data.get('train_data_keys')

        # TODO use asynchrone task for calling ledger

        # TODO put in settings
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        args = '"%(challengeKey)s", "%(algoKey)s", "%(modelKey)s", "%(trainDataKeys)s""' % {
            'challengeKey': challenge_key,
            'algoKey': algo_key,
            'modelKey': model_key,
            'trainDataKeys': ','.join([x for x in train_data_keys]),
        }

        options = {
            'org': org,
            'peer': peer,
            'args': '{"Args":["createTraintuple", ' + args + ']}'
        }
        data, st = invokeLedger(options)

        return data, st

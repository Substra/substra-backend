from rest_framework import serializers, status

from substrapp.conf import conf
from substrapp.models import Data
from substrapp.utils import invokeLedger


class LedgerDataSerializer(serializers.Serializer):

    dataset_key = serializers.CharField(max_length=256)
    size = serializers.IntegerField(min_value=0)
    test_only = serializers.BooleanField()

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        dataset_key = validated_data.get('dataset_key')
        size = validated_data.get('size')
        test_only = validated_data.get('test_only')

        # TODO use asynchrone task for calling ledger

        # TODO put in settings
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        args = '"%(dataHash)s", "%(datasetKey)s", "%(size)s", "%(testOnly)s""' % {
            'dataHash': instance.pkhash,
            'datasetKey': dataset_key,
            'size': size,
            'testOnly': test_only,
        }

        options = {
            'org': org,
            'peer': peer,
            'args': '{"Args":["registerData", ' + args + ']}'
        }
        data, st = invokeLedger(options)

        # TODO : remove when using celery tasks
        #  if not created on ledger, delete from local db
        if st != status.HTTP_201_CREATED:
            Data.objects.get(pk=instance.pkhash).delete()
        else:
            instance.validated = True
            instance.save()
            # pass instance to validated True if ok, else create cron that delete instance.validated = False older than x days

        return data, st

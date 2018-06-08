from rest_framework import serializers, status

from substrapp.conf import conf
from substrapp.models import Problem
from substrapp.utils import invokeLedger


class LedgerProblemSerializer(serializers.Serializer):
    test_data = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                      min_length=1,
                                      max_length=None)
    name = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance_pkhash = self.initial_data.get('instance_pkhash')
        test_data = self.initial_data.get('test_data')

        # TODO use asynchrone task for calling ledger
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]
        options = {
            'org': org,
            'peer': peer,
            'args': '{"Args":["registerProblem", "'+ instance_pkhash + '", "' + str(len(test_data)) + '", "' + ','.join([x for x in test_data]) + '"]}'
        }
        data, st = invokeLedger(options)

        # TODO : remove when using celery tasks
        #  if not created on ledger, delete from local db
        if st != status.HTTP_201_CREATED:
            Problem.objects.get(pk=instance_pkhash).delete()
        # pass instance to validated True if ok, else create cron that delete instance.validated = False older than x days

        return data, st

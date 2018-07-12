from rest_framework import serializers, status

from substrapp.conf import conf
from substrapp.models import Challenge
from substrapp.models.utils import compute_hash
from substrapp.utils import invokeLedger


class LedgerChallengeSerializer(serializers.Serializer):
    test_data_keys = serializers.ListField(child=serializers.CharField(min_length=69, max_length=69),
                                           min_length=1,
                                           max_length=None)
    name = serializers.CharField(min_length=1, max_length=60)
    permissions = serializers.CharField(min_length=1, max_length=60)
    metrics_name = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        metrics_name = validated_data.get('metrics_name')
        permissions = validated_data.get('permissions')
        test_data_keys = validated_data.get('test_data_keys')

        # TODO use asynchrone task for calling ledger

        # TODO put in settings
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        args = '"%(name)s", "%(pkhash)s", "%(descriptionStorageAddress)s", "%(metricsName)s", "%(metricsHash)s", "%(metricsStorageAddress)s", "%(testDataKeys)s", "%(permissions)s"' % {
            'name': name,
            'pkhash': instance.pkhash,
            'descriptionStorageAddress': instance.description.path,
            'metricsName': metrics_name,
            'metricsHash': compute_hash(instance.metrics),
            'metricsStorageAddress': instance.metrics.path,
            'testDataKeys': ','.join([x for x in test_data_keys]),
            'permissions': permissions
        }

        options = {
            'org': org,
            'peer': peer,
            'args': '{"Args":["registerProblem", ' + args + ']}'
        }
        data, st = invokeLedger(options)

        # TODO : remove when using celery tasks
        #  if not created on ledger, delete from local db
        if st != status.HTTP_201_CREATED:
            Challenge.objects.get(pk=instance.pkhash).delete()
        else:
            instance.validated = True
            instance.save()
        # pass instance to validated True if ok, else create cron that delete instance.validated = False older than x days

        return data, st

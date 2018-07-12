from rest_framework import serializers, status

from substrapp.conf import conf
from substrapp.models import Dataset
from substrapp.models.utils import compute_hash
from substrapp.utils import invokeLedger


class LedgerDatasetSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=256)
    type = serializers.CharField(max_length=256)
    problem_keys = serializers.ListField(child=serializers.CharField(min_length=69, max_length=69, allow_blank=True),
                                         max_length=None)
    permissions = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        type = validated_data.get('type')
        permissions = validated_data.get('permissions')
        problem_keys = validated_data.get('problem_keys')

        # TODO use asynchrone task for calling ledger

        # TODO put in settings
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        args = '"%(name)s", "%(openerHash)s", "%(openerStorageAddress)s", "%(type)s", "%(descriptionHash)s", "%(descriptionStorageAddress)s", "%(associatedProblems)s", "%(permissions)s"' % {
            'name': name,
            'openerHash': compute_hash(instance.data_opener),
            'openerStorageAddress': instance.data_opener.path,
            'type': type,
            'descriptionHash': compute_hash(instance.description),
            'descriptionStorageAddress': instance.description.path,
            'associatedProblems': ','.join([x for x in problem_keys]),
            'permissions': permissions
        }

        options = {
            'org': org,
            'peer': peer,
            'args': '{"Args":["registerDataset", ' + args + ']}'
        }
        data, st = invokeLedger(options)

        # TODO : remove when using celery tasks
        #  if not created on ledger, delete from local db
        if st != status.HTTP_201_CREATED:
            Dataset.objects.get(pk=instance.pkhash).delete()
        else:
            instance.validated = True
            instance.save()
            # pass instance to validated True if ok, else create cron that delete instance.validated = False older than x days

        return data, st

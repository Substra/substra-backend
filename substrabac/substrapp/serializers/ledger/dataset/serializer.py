from rest_framework import serializers, status

from django.conf import settings
from rest_framework.reverse import reverse

from .util import createLedgerDataset
from .tasks import createLedgerDatasetAsync

from substrapp.models.utils import compute_hash, get_hash


class LedgerDatasetSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=256)
    type = serializers.CharField(max_length=256)
    challenge_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64, allow_blank=True),
                                           max_length=None)
    permissions = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        type = validated_data.get('type')
        permissions = validated_data.get('permissions')
        challenge_keys = validated_data.get('challenge_keys')

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        # current_site = Site.objects.get_current()
        request = self.context.get('request', None)
        protocol = 'https://' if request.is_secure() else 'http://'
        host = '' if request is None else request.get_host()

        args = '"%(name)s", "%(openerHash)s", "%(openerStorageAddress)s", "%(type)s", "%(descriptionHash)s", "%(descriptionStorageAddress)s", "%(challengeKeys)s", "%(permissions)s"' % {
            'name': name,
            'openerHash': get_hash(instance.data_opener),
            'openerStorageAddress': protocol + host + reverse('substrapp:dataset-opener', args=[instance.pk]),
            'type': type,
            'descriptionHash': get_hash(instance.description),
            'descriptionStorageAddress': protocol + host + reverse('substrapp:dataset-description', args=[instance.pk]),
            'challengeKeys': ','.join([x for x in challenge_keys]),
            'permissions': permissions
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            return createLedgerDataset(args, instance.pkhash, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerDatasetAsync.delay(args, instance.pkhash)

            data = {
                'message': 'Dataset added in local db waiting for validation. The susbtra network has been notified for adding this Dataset'
            }
            st = status.HTTP_202_ACCEPTED
            return data, st

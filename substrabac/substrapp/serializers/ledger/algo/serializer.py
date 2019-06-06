from rest_framework import serializers

from django.conf import settings
from rest_framework.reverse import reverse

from substrapp.utils import get_hash
from .util import createLedgerAlgo
from .tasks import createLedgerAlgoAsync


class LedgerAlgoSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=100)
    permissions = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        permissions = validated_data.get('permissions')

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        host = ''
        protocol = 'http://'
        request = self.context.get('request', None)

        if request:
            protocol = 'https://' if request.is_secure() else 'http://'
            host = request.get_host()

        args = {
            'name': name,
            'hash': get_hash(instance.file),
            'storageAddress': protocol + host + reverse('substrapp:algo-file', args=[instance.pk]),
            'descriptionHash': get_hash(instance.description),
            'descriptionStorageAddress': protocol + host + reverse('substrapp:algo-description', args=[instance.pk]),
            'permissions': permissions
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            data = createLedgerAlgo(args, instance.pkhash, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerAlgoAsync.delay(args, instance.pkhash)
            data = {
                'message': 'Algo added in local db waiting for validation. '
                           'The substra network has been notified for adding this Algo'
            }

        return data

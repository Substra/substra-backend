from rest_framework import serializers, status

from django.conf import settings
from rest_framework.reverse import reverse

from substrapp.utils import get_hash
from .util import createLedgerDataManager
from .tasks import createLedgerDataManagerAsync


class LedgerDataManagerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=30)
    objective_key = serializers.CharField(max_length=256, allow_blank=True, required=False)
    permissions = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        data_type = validated_data.get('type')
        permissions = validated_data.get('permissions')
        objective_key = validated_data.get('objective_key', '')

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        host = ''
        protocol = 'http://'
        request = self.context.get('request', None)

        if request:
            protocol = 'https://' if request.is_secure() else 'http://'
            host = request.get_host()

        args = {
            'name': name,
            'openerHash': get_hash(instance.data_opener),
            'openerStorageAddress': protocol + host + reverse('substrapp:data_manager-opener', args=[instance.pk]),
            'type': data_type,
            'descriptionHash': get_hash(instance.description),
            'descriptionStorageAddress': protocol + host + reverse('substrapp:data_manager-description', args=[instance.pk]),
            'objectiveKey': objective_key,
            'permissions': permissions
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            return createLedgerDataManager(args, instance.pkhash, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerDataManagerAsync.delay(args, instance.pkhash)

            data = {
                'message': 'DataManager added in local db waiting for validation. '
                           'The substra network has been notified for adding this DataManager'
            }
            return data, status.HTTP_202_ACCEPTED

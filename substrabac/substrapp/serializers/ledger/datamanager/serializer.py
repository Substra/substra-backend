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
        type = validated_data.get('type')
        permissions = validated_data.get('permissions')
        objective_key = validated_data.get('objective_key', '')

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        # current_site = Site.objects.get_current()
        request = self.context.get('request', None)
        protocol = 'https://' if request.is_secure() else 'http://'
        host = '' if request is None else request.get_host()

        # args = '"%(name)s", "%(openerHash)s", "%(openerStorageAddress)s", "%(type)s", "%(descriptionHash)s", "%(descriptionStorageAddress)s", "%(objectiveKey)s", "%(permissions)s"' % {
        #     'name': name,
        #     'openerHash': get_hash(instance.data_opener),
        #     'openerStorageAddress': protocol + host + reverse('substrapp:data_manager-opener', args=[instance.pk]),
        #     'type': type,
        #     'descriptionHash': get_hash(instance.description),
        #     'descriptionStorageAddress': protocol + host + reverse('substrapp:data_manager-description', args=[instance.pk]),
        #     'objectiveKey': objective_key,
        #     'permissions': permissions
        # }

        args = [
            name,
            get_hash(instance.data_opener),
            protocol + host + reverse('substrapp:data_manager-opener', args=[instance.pk]),
            type,
            get_hash(instance.description),
            protocol + host + reverse('substrapp:data_manager-description', args=[instance.pk]),
            objective_key,
            permissions
        ]

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            return createLedgerDataManager(args, instance.pkhash, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerDataManagerAsync.delay(args, instance.pkhash)

            data = {
                'message': 'DataManager added in local db waiting for validation. The substra network has been notified for adding this DataManager'
            }
            st = status.HTTP_202_ACCEPTED
            return data, st

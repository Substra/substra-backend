from rest_framework import serializers, status

from django.conf import settings

from .util import createLedgerTesttuple
from .tasks import createLedgerTesttupleAsync


class LedgerTestTupleSerializer(serializers.Serializer):
    traintuple_key = serializers.CharField(min_length=64, max_length=64)

    def create(self, validated_data):
        traintuple_key = validated_data.get('traintuple_key')

        args = '"%(traintupleKey)s"' % {
            'traintupleKey': traintuple_key,
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            return createLedgerTesttuple(args, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerTesttupleAsync.delay(args)

            data = {
                'message': 'The substra network has been notified for adding this Testtuple. Please be aware you won\'t get return values from the ledger. You will need to check manually'
            }
            st = status.HTTP_202_ACCEPTED
            return data, st

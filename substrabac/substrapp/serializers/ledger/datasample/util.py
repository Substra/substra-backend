from __future__ import absolute_import, unicode_literals
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist

from substrapp.models import DataSample
from substrapp.ledger_utils import invokeLedger


def createLedgerDataSample(args, pkhashes, sync=False):

    data, st = invokeLedger(fcn='registerDataSample', args=args, sync=sync)

    try:
        instances = DataSample.objects.filter(pk__in=pkhashes)
    except ObjectDoesNotExist:
        pass
    else:
        # if not created on ledger, delete from local db
        if st not in (status.HTTP_201_CREATED, status.HTTP_408_REQUEST_TIMEOUT):
            instances.delete()
        else:
            # if created on ledger
            if st != status.HTTP_408_REQUEST_TIMEOUT:
                instances.update(validated=True)
                data['validated'] = True

    return data, st


def updateLedgerDataSample(args, sync=False):
    return invokeLedger(fcn='updateDataSample', args=args, sync=sync)

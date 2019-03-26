from __future__ import absolute_import, unicode_literals
from rest_framework import status

from substrapp.models import DataSample
from substrapp.utils import invokeLedger


def createLedgerDataSample(args, pkhashes, sync=False):
    options = {
        'args': '{"Args":["registerDataSample", ' + args + ']}'
    }
    data, st = invokeLedger(options, sync)

    #  if not created on ledger, delete from local db, else pass to validated true
    try:
        instances = DataSample.objects.filter(pk__in=pkhashes)
    except:
        pass
    else:

        # delete if not created
        if st not in (status.HTTP_201_CREATED, status.HTTP_408_REQUEST_TIMEOUT):
            instances.delete()
        else:
            # do not pass to true if still waiting for validation
            if st != status.HTTP_408_REQUEST_TIMEOUT:
                instances.update(validated=True)
                # update data to return
                data['validated'] = True

    return data, st


def updateLedgerDataSample(args, sync=False):
    options = {
        'args': '{"Args":["updateDataSample", ' + args + ']}'
    }
    data, st = invokeLedger(options, sync)

    return data, st

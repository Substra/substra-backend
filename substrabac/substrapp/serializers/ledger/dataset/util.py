from __future__ import absolute_import, unicode_literals
from rest_framework import status

from substrapp.models import Dataset
from substrapp.utils import invokeLedger


def createLedgerDataset(args, pkhash, sync=False):
    options = {
        'args': '{"Args":["registerDataset", ' + args + ']}'
    }
    data, st = invokeLedger(options, sync)

    # if not created on ledger, delete from local db, else pass to validated true
    try:
        instance = Dataset.objects.get(pk=pkhash)
    except:
        pass
    else:
        if st not in (status.HTTP_201_CREATED, status.HTTP_408_REQUEST_TIMEOUT):
            instance.delete()
        else:
            if st != status.HTTP_408_REQUEST_TIMEOUT:
                instance.validated = True
                instance.save()
                # update data to return
                data['validated'] = True

    return data, st


def updateLedgerDataset(args, sync=False):
    options = {
        'args': '{"Args":["updateDataset", ' + args + ']}'
    }
    data, st = invokeLedger(options, sync)

    return data, st

# Create your tasks here
from __future__ import absolute_import, unicode_literals
from rest_framework import status

from substrapp.models import Data
from substrapp.utils import invokeLedger


def createLedgerData(args, pkhashes, sync=False):
    options = {
        'args': '{"Args":["registerData", ' + args + ']}'
    }
    data, st = invokeLedger(options, sync)

    #  if not created on ledger, delete from local db, else pass to validated true
    try:
        instances = Data.objects.filter(pk__in=pkhashes)
    except:
        pass
    else:
        if st != status.HTTP_201_CREATED:
            instances.delete()
        else:
            instances.update(validated=True)
            # update data to return
            data['validated'] = True

    return data, st


def updateLedgerData(args, sync=False):
    options = {
        'args': '{"Args":["updateData", ' + args + ']}'
    }
    data, st = invokeLedger(options, sync)

    return data, st

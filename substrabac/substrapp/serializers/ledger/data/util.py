# Create your tasks here
from __future__ import absolute_import, unicode_literals
from django.conf import settings
from rest_framework import status

from substrapp.models import Data
from substrapp.utils import invokeLedger


def createLedgerData(args, pkhash, sync=False):
    options = {
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["registerData", ' + args + ']}'
    }
    data, st = invokeLedger(options, sync)

    #  if not created on ledger, delete from local db, else pass to validated true
    try:
        instance = Data.objects.get(pk=pkhash)
    except:
        pass
    else:
        if st != status.HTTP_201_CREATED:
            instance.delete()
        else:
            instance.validated = True
            instance.save()

    return data, st

from __future__ import absolute_import, unicode_literals
from rest_framework import status

from substrapp.models import Algo
from substrapp.utils import invokeLedger


def createLedgerAlgo(args, pkhash, sync=False):

    data, st = invokeLedger(fcn='registerAlgo', args=args, sync=sync)

    #  if not created on ledger, delete from local db, else pass to validated true
    try:
        instance = Algo.objects.get(pk=pkhash)
    except Exception:
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

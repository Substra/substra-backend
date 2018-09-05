# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.conf import settings
from rest_framework import status

from substrapp.conf import conf
from substrapp.models import Dataset
from substrapp.utils import invokeLedger


@shared_task
def createLedgerDataset(args, pkhash):
    options = {
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["registerDataset", ' + args + ']}'
    }
    data, st = invokeLedger(options)

    #  if not created on ledger, delete from local db, else pass to validated true
    try:
        instance = Dataset.objects.get(pk=pkhash)
    except:
        pass
    else:
        if st != status.HTTP_201_CREATED:
            instance.delete()
        else:
            instance.validated = True
            instance.save()

    return data, st

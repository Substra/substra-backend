# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.conf import settings


from substrapp.utils import invokeLedger


def createLedgerTraintuple(args):
    options = {
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["createTraintuple", ' + args + ']}'
    }
    data, st = invokeLedger(options)

    return data, st

# Create your tasks here
from __future__ import absolute_import, unicode_literals
from django.conf import settings


from substrapp.utils import invokeLedger


def createLedgerTraintuple(args, sync=False):
    options = {
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["createTraintuple", ' + args + ']}'
    }
    data, st = invokeLedger(options, sync)

    return data, st

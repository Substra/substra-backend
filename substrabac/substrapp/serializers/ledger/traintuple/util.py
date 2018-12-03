# Create your tasks here
from __future__ import absolute_import, unicode_literals


from substrapp.utils import invokeLedger


def createLedgerTraintuple(args, sync=False):
    options = {
        'args': '{"Args":["createTraintuple", ' + args + ']}'
    }
    return invokeLedger(options, sync)

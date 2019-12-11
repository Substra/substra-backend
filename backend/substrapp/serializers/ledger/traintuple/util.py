from __future__ import absolute_import, unicode_literals


from substrapp.ledger_utils import invoke_ledger


def createLedgerTraintuple(args, sync=False):
    return invoke_ledger(fcn='createTraintuple', args=args, sync=sync)

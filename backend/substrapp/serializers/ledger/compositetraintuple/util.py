from __future__ import absolute_import, unicode_literals


from substrapp.ledger_utils import invoke_ledger


def createLedgerCompositeTraintuple(args, sync=False):
    return invoke_ledger(fcn='createCompositeTraintuple', args=args, sync=sync)

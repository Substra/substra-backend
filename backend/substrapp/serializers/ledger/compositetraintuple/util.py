from __future__ import absolute_import, unicode_literals


from substrapp.ledger_utils import invoke_ledger, retry_on_error


@retry_on_error(nbtries=3)
def createLedgerCompositeTraintuple(args, sync=False):
    return invoke_ledger(fcn='createCompositeTraintuple', args=args, sync=sync)

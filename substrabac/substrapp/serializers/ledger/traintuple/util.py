from __future__ import absolute_import, unicode_literals


from substrapp.ledger_utils import invoke_ledger, retry_on_mvcc_error


@retry_on_mvcc_error(nbtries=3)
def createLedgerTraintuple(args, sync=False):
    return invoke_ledger(fcn='createTraintuple', args=args, sync=sync)

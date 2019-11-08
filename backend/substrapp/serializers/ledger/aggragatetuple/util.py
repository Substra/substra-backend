from __future__ import absolute_import, unicode_literals


from substrapp.ledger_utils import invoke_ledger, retry_on_error


@retry_on_error(nbtries=3)
def createLedgerAggregate(args, sync=False):
    return invoke_ledger(fcn='createAggregate', args=args, sync=sync)

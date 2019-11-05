from __future__ import absolute_import, unicode_literals


from substrapp.ledger_utils import invoke_ledger, retry_on_error


@retry_on_error(nbtries=3)
def createLedgerTesttuple(args, sync=False):
    return invoke_ledger(fcn='createTesttuple', args=args, sync=sync)

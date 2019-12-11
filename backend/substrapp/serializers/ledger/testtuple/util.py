from __future__ import absolute_import, unicode_literals


from substrapp.ledger_utils import invoke_ledger


def createLedgerTesttuple(args, sync=False):
    return invoke_ledger(fcn='createTesttuple', args=args, sync=sync)

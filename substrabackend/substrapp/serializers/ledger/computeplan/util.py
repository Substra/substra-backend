from __future__ import absolute_import, unicode_literals


from substrapp.ledger_utils import invoke_ledger


def createLedgerComputePlan(args, sync=False):
    return invoke_ledger(fcn='createComputePlan', args=args, sync=sync, only_pkhash=False)

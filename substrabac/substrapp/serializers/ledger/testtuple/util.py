from __future__ import absolute_import, unicode_literals


from substrapp.utils import invokeLedger


def createLedgerTesttuple(args, sync=False):
    return invokeLedger(fcn='createTesttuple', args=args, sync=sync)

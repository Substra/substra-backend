from __future__ import absolute_import, unicode_literals


from substrapp.utils import invokeLedger


def createLedgerTraintuple(args, sync=False):
    return invokeLedger(fcn='createTraintuple', args=args, cc_pattern='traintuple-creation', sync=sync)

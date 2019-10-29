from __future__ import absolute_import, unicode_literals

from substrapp.models import CompositeAlgo
from substrapp.serializers.ledger.utils import create_ledger_asset


def createLedgerCompositeAlgo(args, pkhash, sync=False):
    return create_ledger_asset(
        model=CompositeAlgo,
        fcn='registerCompositeAlgo',
        args=args,
        pkhash=pkhash,
        sync=sync)

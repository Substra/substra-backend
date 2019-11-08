from __future__ import absolute_import, unicode_literals

from substrapp.models import AggregateAlgo
from substrapp.serializers.ledger.utils import create_ledger_asset


def createLedgerAggregateAlgo(args, pkhash, sync=False):
    return create_ledger_asset(
        model=AggregateAlgo,
        fcn='registerAggregateAlgo',
        args=args,
        pkhash=pkhash,
        sync=sync)

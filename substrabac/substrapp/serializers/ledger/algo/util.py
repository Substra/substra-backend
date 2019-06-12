from __future__ import absolute_import, unicode_literals

from substrapp.models import Algo
from substrapp.serializers.ledger.utils import create_ledger_asset


def createLedgerAlgo(args, pkhash, sync=False):
    return create_ledger_asset(
        model=Algo,
        fcn='registerAlgo',
        args=args,
        pkhash=pkhash,
        sync=sync)

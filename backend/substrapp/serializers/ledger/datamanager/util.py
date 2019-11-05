from __future__ import absolute_import, unicode_literals

from substrapp.models import DataManager
from substrapp.ledger_utils import invoke_ledger

from substrapp.serializers.ledger.utils import create_ledger_asset


def createLedgerDataManager(args, pkhash, sync=False):
    return create_ledger_asset(
        model=DataManager,
        fcn='registerDataManager',
        args=args,
        pkhash=pkhash,
        sync=sync)


def updateLedgerDataManager(args, sync=False):
    return invoke_ledger(fcn='updateDataManager', args=args, sync=sync)

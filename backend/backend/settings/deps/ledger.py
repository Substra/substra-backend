import json
import os

LEDGER_CHANNELS = {
    channel: settings
    for channels in json.loads(os.environ.get("LEDGER_CHANNELS", "[]"))
    for channel, settings in channels.items()
}

LEDGER_MSP_ID = os.environ.get("LEDGER_MSP_ID")

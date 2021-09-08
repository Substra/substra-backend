import os
import json

LEDGER_CHANNELS = {
    channel: settings
    for channels in json.loads(os.getenv('LEDGER_CHANNELS'))
    for channel, settings in channels.items()
}

LEDGER_MSP_ID = os.getenv('LEDGER_MSP_ID')

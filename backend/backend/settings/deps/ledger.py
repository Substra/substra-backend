import json
import os

CHANNELS = {
    channel: settings
    for channels in json.loads(os.environ.get("CHANNELS", "[]"))
    for channel, settings in channels.items()
}

MSP_ID = os.environ.get("MSP_ID")

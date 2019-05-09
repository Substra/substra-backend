import asyncio
import contextlib

from django.conf import settings

import glob

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.util.keyvaluestore import FileKeyValueStore

LEDGER = getattr(settings, 'LEDGER', None)

@contextlib.contextmanager
def get_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()


def onEvent(self, block):
    print(block)

with get_event_loop() as loop:
    channel_name = LEDGER['channel_name']
    chaincode_name = LEDGER['chaincode_name']
    peer = LEDGER['peer']

    client = Client()

    channel = client.new_channel(channel_name)

    target_peer = Peer(name=peer['name'])
    requestor_config = LEDGER['client']

    target_peer.init_with_bundle({'url': f'{peer["host"]}:{peer["docker_port"]}',
                                  'grpcOptions': peer['grpcOptions'],
                                  'tlsCACerts': {'path': peer['tlsCACerts']},
                                  'clientKey': {'path': peer['clientKey']},
                                  'clientCert': {'path': peer['clientCert']},
                                  })

    requestor = create_user(name=requestor_config['name'],
                            org=requestor_config['org'],
                            state_store=FileKeyValueStore(requestor_config['state_store']),
                            msp_id=requestor_config['msp_id'],
                            key_path=glob.glob(requestor_config['key_path'])[0],
                            cert_path=requestor_config['cert_path'])

    channel_event_hub = channel.newChannelEventHub(target_peer,
                                                   requestor)

    # use chaincode event
    stream = channel_event_hub.connect()
    cr = channel_event_hub.registerChaincodeEvent(chaincode_name, 'traintuple-creation', onEvent=onEvent)
    loop.run_until_complete(stream)


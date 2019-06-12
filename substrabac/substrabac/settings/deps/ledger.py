
import os
import asyncio
import glob
import json

from .org import ORG

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.fabric.orderer import Orderer
from hfc.util.keyvaluestore import FileKeyValueStore


LEDGER_CONFIG_FILE = os.environ.get('LEDGER_CONFIG_FILE', f'/substra/conf/{ORG}/substrabac/conf.json')
LEDGER = json.load(open(LEDGER_CONFIG_FILE, 'r'))

LEDGER_SYNC_ENABLED = True

PEER_PORT = LEDGER['peer']['port'][os.environ.get('SUBSTRABAC_PEER_PORT', 'external')]

LEDGER['hfc_requestor'] = create_user(
    name=LEDGER['client']['name'],
    org=LEDGER['client']['org'],
    state_store=FileKeyValueStore(LEDGER['client']['state_store']),
    msp_id=LEDGER['client']['msp_id'],
    key_path=glob.glob(LEDGER['client']['key_path'])[0],
    cert_path=LEDGER['client']['cert_path']
)


def get_hfc_client():

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = Client()
    client.new_channel(LEDGER['channel_name'])

    target_peer = Peer(name=LEDGER['peer']['name'])

    # Need loop
    target_peer.init_with_bundle({
        'url': f'{LEDGER["peer"]["host"]}:{PEER_PORT}',
        'grpcOptions': LEDGER['peer']['grpcOptions'],
        'tlsCACerts': {'path': LEDGER['peer']['tlsCACerts']},
        'clientKey': {'path': LEDGER['peer']['clientKey']},
        'clientCert': {'path': LEDGER['peer']['clientCert']},
    })

    client._peers[LEDGER['peer']['name']] = target_peer

    target_orderer = Orderer(name=LEDGER['orderer']['name'])

    # Need loop
    target_orderer.init_with_bundle({
        'url': f'{LEDGER["orderer"]["host"]}:{LEDGER["orderer"]["port"]}',
        'grpcOptions': LEDGER['orderer']['grpcOptions'],
        'tlsCACerts': {'path': LEDGER['orderer']['ca']},
        'clientKey': {'path': LEDGER['peer']['clientKey']},  # use peer creds (mutual tls)
        'clientCert': {'path': LEDGER['peer']['clientCert']},  # use peer creds (mutual tls)
    })

    client._orderers[LEDGER['orderer']['name']] = target_orderer

    return loop, client


LEDGER['hfc'] = get_hfc_client

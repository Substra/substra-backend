
import os
import asyncio
import glob
import json
import tempfile

from .org import ORG

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.fabric.orderer import Orderer
from hfc.util.keyvaluestore import FileKeyValueStore
from hfc.fabric.block_decoder import decode_fabric_MSP_config, decode_fabric_peers_info, decode_fabric_endpoints


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


def process_discovery(response):
    results = {}
    results['members'] = []

    for res in response.results:
        if res.config_result:
            results['config'] = process_config_result(res.config_result)

        if res.members:
            members = process_members(res.members)
            results['members'].extend(members)

    return results


def process_config_result(config_result):

    results = {'msps': {},
               'orderers': {}}

    for msp_name in config_result.msps:
        results['msps'][msp_name] = decode_fabric_MSP_config(config_result.msps[msp_name].SerializeToString())

    for orderer_msp in config_result.orderers:
        results['orderers'][orderer_msp] = decode_fabric_endpoints(config_result.orderers[orderer_msp].endpoint)

    return results


def process_members(members):
    peers = []
    for msp_name in members.peers_by_org:
        peers.append(decode_fabric_peers_info(members.peers_by_org[msp_name].peers))

    return peers


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

    # Discovery loading
    channel = client.get_channel(LEDGER['channel_name'])
    results = loop.run_until_complete(
        channel._discovery(
            LEDGER['hfc_requestor'],
            client._peers[LEDGER['peer']['name']],
            config=True,
            local=False
        )
    )
    results = process_discovery(results)

    msp_tls_root_certs = {}
    for msp_id, msp_info in results['config']['msps'].items():
        msp_tls_root_certs[msp_id] = msp_info['tls_root_certs'].pop()

    # Load one peer per msp for endorsement transaction
    for msp in results['members']:
        if msp and msp[0]['mspid'] != LEDGER['client']['msp_id']:
            peer_info = msp[0]
            peer = Peer(name=peer_info['mspid'])

            with tempfile.NamedTemporaryFile() as tls_root_cert:
                tls_root_cert.write(msp_tls_root_certs[peer_info['mspid']])
                tls_root_cert.flush()

                # Need loop
                peer.init_with_bundle({
                    'url': peer_info['endpoint'],
                    'grpcOptions': {
                        'grpc-max-send-message-length': 15,
                        'grpc.ssl_target_name_override': peer_info['endpoint'].split(':')[0]
                    },
                    'tlsCACerts': {'path': tls_root_cert.name},
                    'clientKey': {'path': LEDGER['peer']['clientKey']},  # use peer creds (mutual tls)
                    'clientCert': {'path': LEDGER['peer']['clientCert']},  # use peer creds (mutual tls)
                })

            client._peers[peer_info['mspid']] = peer

    # Load one orderer
    orderer_mspid, orderer_info = list(results['config']['orderers'].items())[0]
    orderer_endpoint = f'{orderer_info[0]["host"]}:{orderer_info[0]["port"]}'

    target_orderer = Orderer(name=orderer_mspid)

    with tempfile.NamedTemporaryFile() as tls_root_cert:
        tls_root_cert.write(msp_tls_root_certs[orderer_mspid])
        tls_root_cert.flush()

        # Need loop
        target_orderer.init_with_bundle({
            'url': orderer_endpoint,
            'grpcOptions': {
                'grpc-max-send-message-length': 15,
                'grpc.ssl_target_name_override': orderer_info[0]['host']
            },
            'tlsCACerts': {'path': tls_root_cert.name},
            'clientKey': {'path': LEDGER['peer']['clientKey']},  # use peer creds (mutual tls)
            'clientCert': {'path': LEDGER['peer']['clientCert']},  # use peer creds (mutual tls)
        })

    client._orderers[orderer_mspid] = target_orderer

    return loop, client


LEDGER['hfc'] = get_hfc_client

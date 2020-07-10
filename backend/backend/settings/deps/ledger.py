import os
import base64
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

SUBSTRA_FOLDER = os.getenv('SUBSTRA_PATH', '/substra')
LEDGER_CONFIG_FILE = os.environ.get('LEDGER_CONFIG_FILE', f'{SUBSTRA_FOLDER}/conf/{ORG}/substra-backend/conf.json')
LEDGER = json.load(open(LEDGER_CONFIG_FILE, 'r'))
LEDGER_SYNC_ENABLED = True
LEDGER_CALL_RETRY = True
LEDGER_MAX_RETRY_TIMEOUT = 5
LEDGER_WAIT_FOR_EVENT_TIMEOUT = int(os.getenv('LEDGER_WAIT_FOR_EVENT_TIMEOUT', '45'))
LEDGER_INVOKE_STRATEGY = os.getenv('LEDGER_INVOKE_STRATEGY', 'ALL').upper() # possible values SELF / ALL
LEDGER_QUERY_STRATEGY = os.getenv('LEDGER_QUERY_STRATEGY', 'SELF').upper() # possible values SELF / ALL
LEDGER['requestor'] = create_user(
    name=LEDGER['client']['name'],
    org=LEDGER['client']['org'],
    state_store=FileKeyValueStore(LEDGER['client']['state_store']),
    msp_id=LEDGER['client']['msp_id'],
    key_path=glob.glob(LEDGER['client']['key_path'])[0],
    cert_path=LEDGER['client']['cert_path']
)
PEER_PORT = LEDGER['peer']['port'][os.environ.get('BACKEND_PEER_PORT', 'external')]


def get_hfc_client(channel_name):

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = Client()

    # Add peer from backend ledger config file
    peer = Peer(name=LEDGER['peer']['name'])
    peer.init_with_bundle({
        'url': f'{LEDGER["peer"]["host"]}:{PEER_PORT}',
        'grpcOptions': LEDGER['peer']['grpcOptions'],
        'tlsCACerts': {'path': LEDGER['peer']['tlsCACerts']},
        'clientKey': {'path': LEDGER['peer']['clientKey']},
        'clientCert': {'path': LEDGER['peer']['clientCert']},
    })
    client._peers[LEDGER['peer']['name']] = peer

    # Check peer has joined channel

    response = loop.run_until_complete(
        client.query_channels(
            requestor=LEDGER['requestor'],
            peers=[peer],
            decode=True
        )
    )

    channels = [ch.channel_id for ch in response.channels]

    if not channel_name in channels:
        raise Exception(f'Peer has not joined channel: {channel_name}')

    channel = client.new_channel(channel_name)

    # Check chaincode is instantiated in the channel

    responses = loop.run_until_complete(
        client.query_instantiated_chaincodes(
            requestor=LEDGER['requestor'],
            channel_name=channel_name,
            peers=[peer],
            decode=True
        )
    )

    chaincodes = [cc.name
                  for resp in responses
                  for cc in resp.chaincodes]

    if not LEDGER['chaincode_name'] in chaincodes:
        raise Exception(f'Chaincode : {LEDGER["chaincode_name"]}'
                        f' is not instantiated in the channel :  {channel_name}')

    # Discover orderers and peers from channel discovery
    results = loop.run_until_complete(
        channel._discovery(
            LEDGER['requestor'],
            peer,
            config=True,
            local=False,
            interests=[{'chaincodes': [{'name': LEDGER['chaincode_name']}]}]
        )
    )

    results = deserialize_discovery(results)

    update_client_with_discovery(client, results)

    return loop, client


LEDGER['hfc'] = get_hfc_client


def update_client_with_discovery(client, discovery_results):

    # Get all msp tls root cert files
    tls_root_certs = {}

    for mspid, msp_info in discovery_results['config']['msps'].items():
        tls_root_certs[mspid] = base64.decodebytes(
            msp_info['tls_root_certs'].pop().encode()
        )

    # Load one peer per msp for endorsing transaction
    for msp in discovery_results['members']:
        if not len(msp):
            continue

        peer_info = msp[0]

        if peer_info['mspid'] != LEDGER['client']['msp_id']:
            peer = Peer(name=peer_info['mspid'])

            with tempfile.NamedTemporaryFile() as tls_root_cert:
                tls_root_cert.write(tls_root_certs[peer_info['mspid']])
                tls_root_cert.flush()

                url = peer_info['endpoint']
                external_port = os.environ.get('BACKEND_PEER_PORT_EXTERNAL', None)
                # use case for external development
                if external_port:
                    url = f"{peer_info['endpoint'].split(':')[0]}:{external_port}"
                peer.init_with_bundle({
                    'url': url,
                    'grpcOptions': {
                        'grpc.ssl_target_name_override': peer_info['endpoint'].split(':')[0],
                        'grpc.max_send_message_length': -1,
                        'grpc.max_receive_message_length': -1
                    },
                    'tlsCACerts': {'path': tls_root_cert.name},
                    'clientKey': {'path': LEDGER['peer']['clientKey']},  # use peer creds (mutual tls)
                    'clientCert': {'path': LEDGER['peer']['clientCert']},  # use peer creds (mutual tls)
                })

            client._peers[peer_info['mspid']] = peer

    # Load one orderer for broadcasting transaction
    orderer_mspid, orderer_info = list(discovery_results['config']['orderers'].items())[0]

    orderer = Orderer(name=orderer_mspid)

    with tempfile.NamedTemporaryFile() as tls_root_cert:
        tls_root_cert.write(tls_root_certs[orderer_mspid])
        tls_root_cert.flush()

        # Need loop
        orderer.init_with_bundle({
            'url': f"{orderer_info[0]['host']}:{orderer_info[0]['port']}",
            'grpcOptions': {
                'grpc.ssl_target_name_override': orderer_info[0]['host'],
                'grpc.max_send_message_length': -1,
                'grpc.max_receive_message_length': -1
            },
            'tlsCACerts': {'path': tls_root_cert.name},
            'clientKey': {'path': LEDGER['peer']['clientKey']},  # use peer creds (mutual tls)
            'clientCert': {'path': LEDGER['peer']['clientCert']},  # use peer creds (mutual tls)
        })

    client._orderers[orderer_mspid] = orderer


def deserialize_discovery(response):
    results = {
        'config': None,
        'members': [],
        'cc_query_res': None
    }

    for res in response.results:
        if res.config_result and res.config_result.msps and res.config_result.orderers:
            results['config'] = deserialize_config(res.config_result)

        if res.members:
            results['members'].extend(deserialize_members(res.members))

        if res.cc_query_res and res.cc_query_res.content:
            results['cc_query_res'] = deserialize_cc_query_res(res.cc_query_res)

    return results


def deserialize_config(config_result):

    results = {'msps': {},
               'orderers': {}}

    for mspid in config_result.msps:
        results['msps'][mspid] = decode_fabric_MSP_config(
            config_result.msps[mspid].SerializeToString()
        )

    for mspid in config_result.orderers:
        results['orderers'][mspid] = decode_fabric_endpoints(
            config_result.orderers[mspid].endpoint
        )

    return results


def deserialize_members(members):
    peers = []

    for mspid in members.peers_by_org:
        peer = decode_fabric_peers_info(
            members.peers_by_org[mspid].peers
        )
        peers.append(peer)

    return peers


def deserialize_cc_query_res(cc_query_res):
    cc_queries = []

    for cc_query_content in cc_query_res.content:
        cc_query = {
            'chaincode': cc_query_content.chaincode,
            'endorsers_by_groups': {},
            'layouts': []
        }

        for group in cc_query_content.endorsers_by_groups:
            peers = decode_fabric_peers_info(
                cc_query_content.endorsers_by_groups[group].peers
            )

            cc_query['endorsers_by_groups'][group] = peers

        for layout_content in cc_query_content.layouts:
            layout = {
                'quantities_by_group': {
                    group: int(layout_content.quantities_by_group[group])
                    for group in layout_content.quantities_by_group
                }
            }
            cc_query['layouts'].append(layout)

        cc_queries.append(cc_query)

    return cc_queries

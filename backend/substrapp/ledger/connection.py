import base64
import contextlib
import asyncio
import glob
import tempfile

from django.conf import settings
from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.fabric.orderer import Orderer
from hfc.util.keyvaluestore import FileKeyValueStore
from hfc.fabric.block_decoder import decode_fabric_MSP_config, decode_fabric_peers_info, decode_fabric_endpoints

user = None


def ledger_grpc_options(hostname):
    return {
        'grpc.max_send_message_length': settings.LEDGER_GRPC_MAX_SEND_MESSAGE_LENGTH,
        'grpc.max_receive_message_length': settings.LEDGER_GRPC_MAX_RECEIVE_MESSAGE_LENGTH,
        'grpc.keepalive_timeout_ms': settings.LEDGER_GRPC_KEEPALIVE_TIMEOUT_MS,
        'grpc.http2.max_pings_without_data': settings.LEDGER_GRPC_HTTP2_MAX_PINGS_WITHOUT_DATA,
        'grpc.keepalive_permit_without_calls': settings.LEDGER_GRPC_KEEPALIVE_PERMIT_WITHOUT_CALLS,
        'grpc.ssl_target_name_override': hostname
    }


@contextlib.contextmanager
def get_hfc(channel_name):
    loop, client, user = _get_hfc(channel_name)
    try:
        yield (loop, client, user)
    finally:
        loop.run_until_complete(
            client.close_grpc_channels()
        )
        del client
        loop.close()


def _get_hfc(channel_name):
    global user

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if not user:
        # Only call `create_user` once in the lifetime of the application.
        # Calling `create_user` twice breaks thread-safety (bug in fabric-sdk-py)
        user = create_user(
            name=settings.LEDGER_USER_NAME,
            org=settings.ORG_NAME,
            state_store=FileKeyValueStore(settings.LEDGER_CLIENT_STATE_STORE),
            msp_id=settings.LEDGER_MSP_ID,
            key_path=glob.glob(settings.LEDGER_CLIENT_KEY_PATH)[0],
            cert_path=settings.LEDGER_CLIENT_CERT_PATH
        )

    client = Client()

    # Add peer from backend ledger config file
    peer = Peer(name=settings.LEDGER_PEER_NAME)
    peer.init_with_bundle({
        'url': f'{settings.LEDGER_PEER_HOST}:{settings.LEDGER_PEER_PORT}',
        'grpcOptions': ledger_grpc_options(settings.LEDGER_PEER_HOST),
        'tlsCACerts': {'path': settings.LEDGER_PEER_TLS_CA_CERTS},
        'clientKey': {'path': settings.LEDGER_PEER_TLS_CLIENT_KEY},
        'clientCert': {'path': settings.LEDGER_PEER_TLS_CLIENT_CERT},
    })
    client._peers[settings.LEDGER_PEER_NAME] = peer

    # Check peer has joined channel

    response = loop.run_until_complete(
        client.query_channels(
            requestor=user,
            peers=[peer],
            decode=True
        )
    )

    channels = [ch.channel_id for ch in response.channels]

    if channel_name not in channels:
        raise Exception(f'Peer has not joined channel: {channel_name}')

    channel = client.new_channel(channel_name)
    # chaincode_name = settings.LEDGER_CHANNELS[channel_name]['chaincode']['name']

    # /!\ New chaincode lifecycle.

    # Check chaincode is committed in the channel
    # responses = loop.run_until_complete(
    #     client.query_committed_chaincodes(
    #         requestor=user,
    #         channel_name=channel_name,
    #         peers=[peer],
    #         decode=True
    #     )
    # )
    # chaincodes = [cc.name
    #               for resp in responses
    #               for cc in resp.chaincode_definitions]
    # if chaincode_name not in chaincodes:
    #     raise Exception(f'Chaincode : {chaincode_name}'
    #                     f' is not committed in the channel :  {channel_name}')

    # Discover orderers and peers from channel discovery
    results = loop.run_until_complete(
        channel._discovery(
            user,
            peer,
            config=True,
            local=False,
            interests=[{'chaincodes': [{'name': "_lifecycle"}]}]
        )
    )

    results = _deserialize_discovery(results)

    _update_client_with_discovery(client, results)

    return loop, client, user


def _update_client_with_discovery(client, discovery_results):

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

        if peer_info['mspid'] != settings.LEDGER_MSP_ID:
            peer = Peer(name=peer_info['mspid'])

            with tempfile.NamedTemporaryFile() as tls_root_cert:
                tls_root_cert.write(tls_root_certs[peer_info['mspid']])
                tls_root_cert.flush()

                url = peer_info['endpoint']
                peer.init_with_bundle({
                    'url': url,
                    'grpcOptions': ledger_grpc_options(peer_info['endpoint'].split(':')[0]),
                    'tlsCACerts': {'path': tls_root_cert.name},
                    'clientKey': {'path': settings.LEDGER_PEER_TLS_CLIENT_KEY},
                    'clientCert': {'path': settings.LEDGER_PEER_TLS_CLIENT_CERT}
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
            'grpcOptions': ledger_grpc_options(orderer_info[0]['host']),
            'tlsCACerts': {'path': tls_root_cert.name},
            'clientKey': {'path': settings.LEDGER_PEER_TLS_CLIENT_KEY},
            'clientCert': {'path': settings.LEDGER_PEER_TLS_CLIENT_CERT}
        })

    client._orderers[orderer_mspid] = orderer


def _deserialize_discovery(response):
    results = {
        'config': None,
        'members': [],
        'cc_query_res': None
    }

    for res in response.results:
        if res.config_result and res.config_result.msps and res.config_result.orderers:
            results['config'] = _deserialize_config(res.config_result)

        if res.members:
            results['members'].extend(_deserialize_members(res.members))

        if res.cc_query_res and res.cc_query_res.content:
            results['cc_query_res'] = _deserialize_cc_query_res(res.cc_query_res)

    return results


def _deserialize_config(config_result):

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


def _deserialize_members(members):
    peers = []

    for mspid in members.peers_by_org:
        peer = decode_fabric_peers_info(
            members.peers_by_org[mspid].peers
        )
        peers.append(peer)

    return peers


def _deserialize_cc_query_res(cc_query_res):
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

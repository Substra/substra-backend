from hfc.fabric import Client
from hfc.fabric.channel.channel import Channel
from hfc.fabric.block_decoder import decode_fabric_MSP_config, decode_fabric_peers_info, decode_fabric_endpoints
from hfc.fabric.peer import create_peer
from hfc.fabric.user import create_user
from hfc.util.crypto.crypto import ecies
from hfc.util.keyvaluestore import FileKeyValueStore

import pprint
import glob

peer_config = {'clientKey': {'path': '/substra/data/orgs/owkin/tls/peer1/cli-client.key'},
               'clientServer': {'path': '/substra/data/orgs/owkin/tls/peer1/cli-client.crt'},
               'eventUrl': 'peer1-owkin:7053',
               'grpcOptions': {'grpc.http2.keepalive_time': 15,
                               'grpc.ssl_target_name_override': 'peer1-owkin'},
               'tlsCACerts': {
                   'path': '/substra/data/orgs/owkin/ca-cert.pem'},
               'url': 'peer1-owkin:7051'}

peer1_owkin = create_peer(endpoint=peer_config['url'],
                          tls_cacerts=peer_config['tlsCACerts']['path'],
                          client_key=peer_config['clientKey']['path'],
                          client_cert=peer_config['clientServer']['path'],
                          opts=[(k, v) for k, v in peer_config['grpcOptions'].items()])

key_path = glob.glob('/substra/data/orgs/owkin/admin/msp/keystore/*')[0]
cert_path = '/substra/data/orgs/owkin/admin/msp/signcerts/cert.pem'

admin_owkin = create_user(name='admin',
                          org='owkin',
                          state_store=FileKeyValueStore('/tmp/kvs/'),
                          msp_id='owkinMSP',
                          key_path=key_path,
                          cert_path=cert_path)


client = Client()
client._crypto_suite = ecies()

print(client.query_peers(admin_owkin, peer1_owkin))
print(client.query_peers(admin_owkin, peer1_owkin, channel='mychannel', local=False))

response = Channel('mychannel', '')._discovery(admin_owkin, peer1_owkin, client.crypto_suite, config=True, local=False)


def process_config_result(config_result):

    results = {'msps': {},
               'orderers': {}}

    for msp_name in config_result.msps:
        results['msps'][msp_name] = decode_fabric_MSP_config(config_result.msps[msp_name].SerializeToString())

    for orderer_msp in config_result.orderers:
        results['orderers'][orderer_msp] = decode_fabric_endpoints(config_result.orderers[orderer_msp].endpoint)

    return results


def process_cc_query_res(cc_query_res):
    pass


def process_members(members):
    peers = []
    for msp_name in members.peers_by_org:
        peers.append(decode_fabric_peers_info(members.peers_by_org[msp_name].peers))
    return peers


results = {}
for res in response.results:
    # print(res)
        print('-' * 100)
        print('Error')
        pprint.pprint(res.error)
        print('-' * 50)
        print('Config result')
        pprint.pprint(process_config_result(res.config_result), indent=2)
        # print(f'Chaincode Query result : {res.cc_query_res}')
        print('Members')
        pprint.pprint(process_members(res.members), indent=2)
        print('#' * 100)

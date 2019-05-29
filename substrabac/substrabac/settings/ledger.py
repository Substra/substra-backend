
import os
import asyncio
import glob
import json

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.fabric.orderer import Orderer
from hfc.util.keyvaluestore import FileKeyValueStore


ORG = os.environ.get('SUBSTRABAC_ORG', 'substra')

LEDGER = json.load(open(f'/substra/conf/{ORG}/substrabac/conf.json', 'r'))

HLF_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(HLF_LOOP)

channel_name = LEDGER['channel_name']
chaincode_name = LEDGER['chaincode_name']
peer = LEDGER['peer']
peer_port = peer["port"][os.environ.get('SUBSTRABAC_PEER_PORT', 'external')]
orderer = LEDGER['orderer']

requestor_config = LEDGER['client']

CLIENT = Client()
CLIENT.new_channel(channel_name)

REQUESTOR = create_user(name=requestor_config['name'],
                        org=requestor_config['org'],
                        state_store=FileKeyValueStore(requestor_config['state_store']),
                        msp_id=requestor_config['msp_id'],
                        key_path=glob.glob(requestor_config['key_path'])[0],
                        cert_path=requestor_config['cert_path'])

target_peer = Peer(name=peer['name'])

# Need loop
target_peer.init_with_bundle({'url': f'{peer["host"]}:{peer_port}',
                              'grpcOptions': peer['grpcOptions'],
                              'tlsCACerts': {'path': peer['tlsCACerts']},
                              'clientKey': {'path': peer['clientKey']},
                              'clientCert': {'path': peer['clientCert']},
                              })
CLIENT._peers[peer['name']] = target_peer

target_orderer = Orderer(name=orderer['name'])

# Need loop
target_orderer.init_with_bundle({'url': f'{orderer["host"]}:{orderer["port"]}',
                                 'grpcOptions': orderer['grpcOptions'],
                                 'tlsCACerts': {'path': orderer['ca']},
                                 'clientKey': {'path': peer['clientKey']},  # use peer creds (mutual tls)
                                 'clientCert': {'path': peer['clientCert']},  # use peer creds (mutual tls)
                                 })
CLIENT._orderers[orderer['name']] = target_orderer

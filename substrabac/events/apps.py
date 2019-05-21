import asyncio
import json
import multiprocessing
import os

import glob

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.util.keyvaluestore import FileKeyValueStore


ORG = os.environ.get('SUBSTRABAC_ORG', 'substra')

try:
    LEDGER = json.load(open(f'/substra/conf/{ORG}/substrabac/conf.json', 'r'))
except:
    pass


def onEvent(block):
    payload = json.loads(
        block['data']['data'][0]['payload']['data']['actions'][0]['payload']['action']['proposal_response_payload'][
            'extension']['events']['payload'])
    print(payload)
    worker_queue = f"{LEDGER['name']}.worker"

    # TODO check if owner is the one to run task, wait for chaincode to send full traintuple with key inside
    # if payload['status'] == 'todo':
    #     prepareTrainTuple.apply_async((payload,), queue=worker_queue)


def wait():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    channel_name = LEDGER['channel_name']
    chaincode_name = LEDGER['chaincode_name']
    peer = LEDGER['peer']

    peer_port = peer["port"][os.environ.get('SUBSTRABAC_PEER_PORT', 'external')]

    client = Client()

    channel = client.new_channel(channel_name)

    target_peer = Peer(name=peer['name'])
    requestor_config = LEDGER['client']

    target_peer.init_with_bundle({'url': f'{peer["host"]}:{peer_port}',
                                  'grpcOptions': peer['grpcOptions'],
                                  'tlsCACerts': {'path': peer['tlsCACerts']},
                                  'clientKey': {'path': peer['clientKey']},
                                  'clientCert': {'path': peer['clientCert']},
                                  })

    try:
        # can fail
        requestor = create_user(name=requestor_config['name'],
                            org=requestor_config['org'],
                            state_store=FileKeyValueStore(requestor_config['state_store']),
                            msp_id=requestor_config['msp_id'],
                            key_path=glob.glob(requestor_config['key_path'])[0],
                            cert_path=requestor_config['cert_path'])
    except:
        pass
    else:
        channel_event_hub = channel.newChannelEventHub(target_peer, requestor)

        # use chaincode event

        # uncomment this line if you want to replay blocks from the beginning for debugging purposes
        # stream = channel_event_hub.connect(start=0, filtered=False)
        stream = channel_event_hub.connect(filtered=False)

        channel_event_hub.registerChaincodeEvent(chaincode_name, 'traintuple-creation', onEvent=onEvent)
        loop.run_until_complete(stream)
    finally:
        loop.close()


if __name__ == '__main__':

    p1 = multiprocessing.Process(target=wait)
    # always wait
    p1.start()

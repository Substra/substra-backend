import asyncio
import json
import multiprocessing

from django.apps import AppConfig

from django.conf import settings

import glob

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.util.keyvaluestore import FileKeyValueStore


LEDGER = getattr(settings, 'LEDGER', None)

def onEvent(block):
    payload = json.loads(
        block['data']['data'][0]['payload']['data']['actions'][0]['payload']['action']['proposal_response_payload'][
            'extension']['events']['payload'])
    print(payload)
    worker_queue = f"{settings.LEDGER['name']}.worker"

    # TODO check if owner is the one to run task
    # if payload['status'] == 'todo':
    #     prepareTrainTuple.apply_async((payload,), queue=worker_queue)


def wait():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    channel_name = LEDGER['channel_name']
    chaincode_name = LEDGER['chaincode_name']
    peer = LEDGER['peer']

    client = Client()

    channel = client.new_channel(channel_name)

    target_peer = Peer(name=peer['name'])
    requestor_config = LEDGER['client']

    target_peer.init_with_bundle({'url': f'{peer["host"]}:{peer["port"]}',
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

    channel_event_hub = channel.newChannelEventHub(target_peer, requestor)

    # use chaincode event
    stream = channel_event_hub.connect(start=0, filtered=False)
    channel_event_hub.registerChaincodeEvent(chaincode_name, 'traintuple-creation', onEvent=onEvent)

    loop.run_until_complete(stream)
    loop.close()


class EventsConfig(AppConfig):
    name = 'events'

    def ready(self):
        p1 = multiprocessing.Process(target=wait)
        # always wait
        p1.start()

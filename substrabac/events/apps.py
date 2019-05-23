import asyncio
import json
import logging
import multiprocessing
import os

from django.apps import AppConfig

from django.conf import settings

import glob

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.util.keyvaluestore import FileKeyValueStore

from substrapp.tasks import prepareTuple
from substrapp.utils import get_hash, get_event_loop

LEDGER = getattr(settings, 'LEDGER', None)


def get_block_payload(block):
    payload = json.loads(
        block['data']['data'][0]['payload']['data']['actions'][0]['payload']['action']['proposal_response_payload'][
            'extension']['events']['payload'])
    return payload


def onTupleEvent(block):
    payload = get_block_payload(block)

    worker_queue = f"{LEDGER['name']}.worker"
    try:
        data_owner = get_hash(LEDGER['signcert'])
    except Exception as e:
        logging.error(e, exc_info=True)
    else:
        if data_owner == payload['dataset']['worker']:
            tuple_type, model_type = (None, None)
            if 'inModels' in payload:
                tuple_type, model_type = ('traintuple', 'inModels')
            elif 'model' in payload:
                tuple_type, model_type = ('testtuple', 'model')

            if tuple_type is not None and model_type is not None:
                prepareTuple.apply_async((payload, tuple_type, model_type), queue=worker_queue)


def wait():
    with get_event_loop() as loop:
        channel_name = LEDGER['channel_name']
        chaincode_name = LEDGER['chaincode_name']
        peer = LEDGER['peer']

        peer_port = peer["port"][os.environ.get('SUBSTRABAC_PEER_PORT', 'external')]

        client = Client()

        channel = client.new_channel(channel_name)

        target_peer = Peer(name=peer['name'])
        requestor_config = LEDGER['client']

        target_peer.init_with_bundle({
            'url': f'{peer["host"]}:{peer_port}',
            'grpcOptions': peer['grpcOptions'],
            'tlsCACerts': {'path': peer['tlsCACerts']},
            'clientKey': {'path': peer['clientKey']},
            'clientCert': {'path': peer['clientCert']},
        })

        try:
            # can fail
            requestor = create_user(
                name=requestor_config['name'],
                org=requestor_config['org'],
                state_store=FileKeyValueStore(requestor_config['state_store']),
                msp_id=requestor_config['msp_id'],
                key_path=glob.glob(requestor_config['key_path'])[0],
                cert_path=requestor_config['cert_path']
            )
        except:
            pass
        else:
            channel_event_hub = channel.newChannelEventHub(target_peer,
                                                           requestor)

            # use chaincode event

            # uncomment this line if you want to replay blocks from the beginning for debugging purposes
            # stream = channel_event_hub.connect(start=0, filtered=False)
            stream = channel_event_hub.connect(filtered=False)

            channel_event_hub.registerChaincodeEvent(chaincode_name,
                                                     'traintuple-creation',
                                                     onEvent=onTupleEvent)
            channel_event_hub.registerChaincodeEvent(chaincode_name,
                                                     'testtuple-creation',
                                                     onEvent=onTupleEvent)
            loop.run_until_complete(stream)


class EventsConfig(AppConfig):
    name = 'events'

    def ready(self):
        # always wait
        p1 = multiprocessing.Process(target=wait)
        p1.start()

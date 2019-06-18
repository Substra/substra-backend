import asyncio
import json
import multiprocessing
import os
import contextlib

from django.apps import AppConfig

from django.conf import settings

import glob

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.util.keyvaluestore import FileKeyValueStore
from hfc.protos.peer.transaction_pb2 import TxValidationCode

from substrapp.tasks.tasks import prepare_tuple
from substrapp.utils import get_hash

LEDGER = getattr(settings, 'LEDGER', None)


def get_tuple_type(payload):

    tuple_type = None

    if 'inModels' in payload:
        tuple_type = 'traintuple'
    elif 'model' in payload:
        tuple_type = 'testtuple'

    return tuple_type


@contextlib.contextmanager
def get_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()


def get_block_payload(block):
    payload = json.loads(
        block['data']['data'][0]['payload']['data']['actions'][0]['payload']['action']['proposal_response_payload'][
            'extension']['events']['payload'])
    return payload


def log_tuple_status(block, tuple_type, key, event_type):

    try:
        meta = block['metadata']['metadata'][-1]
        if isinstance(meta, list):
            meta = int(meta.pop())
        status = TxValidationCode.Name(meta)
    except Exception:
        print(f'[ChaincodeEvent] Received {tuple_type} "{event_type}" (key: "{key}")')
    else:
        print(f'[ChaincodeEvent] Received {tuple_type} "{event_type}" (key: "{key}") with status: {status}')


def on_tuple_created(block):
    payload = get_block_payload(block)
    tuple_type = get_tuple_type(payload)
    log_tuple_status(block, tuple_type, payload['key'], 'created')


def on_tuple_ready(block):
    payload = get_block_payload(block)
    tuple_type = get_tuple_type(payload)
    log_tuple_status(block, tuple_type, payload['key'], 'ready')

    worker_queue = f"{LEDGER['name']}.worker"
    data_owner = get_hash(LEDGER['signcert'])

    if data_owner == payload['dataset']['worker'] and tuple_type is not None:
        prepare_tuple.apply_async(
            (payload, tuple_type),
            task_id=payload['key'],
            queue=worker_queue
        )


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
                name=requestor_config['name'] + '_events',
                org=requestor_config['org'],
                state_store=FileKeyValueStore(requestor_config['state_store']),
                msp_id=requestor_config['msp_id'],
                key_path=glob.glob(requestor_config['key_path'])[0],
                cert_path=requestor_config['cert_path']
            )
        except BaseException:
            pass
        else:
            channel_event_hub = channel.newChannelEventHub(target_peer,
                                                           requestor)

            # use chaincode event

            # uncomment this line if you want to replay blocks from the beginning for debugging purposes
            # stream = channel_event_hub.connect(start=0, filtered=False)
            stream = channel_event_hub.connect(filtered=False)

            channel_event_hub.registerChaincodeEvent(chaincode_name,
                                                     'traintuple-ready',
                                                     onEvent=on_tuple_ready)
            channel_event_hub.registerChaincodeEvent(chaincode_name,
                                                     'testtuple-ready',
                                                     onEvent=on_tuple_ready)

            channel_event_hub.registerChaincodeEvent(chaincode_name,
                                                     'traintuple-created',
                                                     onEvent=on_tuple_created)
            channel_event_hub.registerChaincodeEvent(chaincode_name,
                                                     'testtuple-created',
                                                     onEvent=on_tuple_created)

            loop.run_until_complete(stream)


class EventsConfig(AppConfig):
    name = 'events'

    def ready(self):
        # always wait
        p1 = multiprocessing.Process(target=wait)
        p1.start()

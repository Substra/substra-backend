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
from substrapp.utils import get_owner

from celery.result import AsyncResult

import logging

LEDGER = getattr(settings, 'LEDGER', None)


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


def on_tuples(block):
    try:
        meta = block['metadata']['metadata'][-1]
        if isinstance(meta, list):
            meta = int(meta.pop())
        tx_validation_code = TxValidationCode.Name(meta)
    except Exception:
        tx_validation_code = None

    payload = get_block_payload(block)

    for tuple_type, _tuples in payload.items():
        if _tuples:
            for _tuple in _tuples:
                tuple_key = _tuple['key']
                tuple_status = _tuple['status']

                logging.info(f'[ChaincodeEvent] Received {tuple_type} "{tuple_status}" '
                             f'(key: "{tuple_key}") with tx status: {tx_validation_code}')

                if tuple_status == 'todo':
                    launch_tuple(_tuple, tuple_type)


def launch_tuple(_tuple, tuple_type):

    worker_queue = f"{LEDGER['name']}.worker"
    data_owner = get_owner()

    if data_owner == _tuple['dataset']['worker'] and tuple_type is not None:
        tkey = _tuple['key']
        if AsyncResult(tkey).state == 'PENDING':
            prepare_tuple.apply_async(
                (_tuple, tuple_type),
                task_id=tkey,
                queue=worker_queue
            )
        else:
            print(f'[ChaincodeEvent] Tuple task ({tkey}) already exists')


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
                                                     'tuples-updated',
                                                     onEvent=on_tuples)
            loop.run_until_complete(stream)


class EventsConfig(AppConfig):
    name = 'events'

    def ready(self):
        # always wait
        p1 = multiprocessing.Process(target=wait)
        p1.start()

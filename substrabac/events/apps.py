import asyncio
import json
import logging
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
from substrapp.ledger_utils import get_hfc

from celery.result import AsyncResult

logger = logging.getLogger(__name__)
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
    owner = get_owner()
    worker_queue = f"{LEDGER['name']}.worker"

    for tuple_type, _tuples in payload.items():
        if not _tuples:
            continue

        for _tuple in _tuples:
            key = _tuple['key']
            status = _tuple['status']

            logger.info(f'Processing task {key}: type={tuple_type} status={status}'
                        f' with tx status: {tx_validation_code}')

            if status != 'todo':
                continue

            if tuple_type is None:
                continue

            tuple_owner = _tuple['dataset']['worker']
            if tuple_owner != owner:
                logger.debug(f'Skipping task {key}: owner does not match'
                             f' ({tuple_owner} vs {owner})')
                continue

            if AsyncResult(key).state != 'PENDING':
                logger.info(f'Skipping task {key}: already exists')
                continue

            prepare_tuple.apply_async(
                (_tuple, tuple_type),
                task_id=key,
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
                                                     'tuples-updated',
                                                     onEvent=on_tuples)
            loop.run_until_complete(stream)


class EventsConfig(AppConfig):
    name = 'events'

    def ready(self):

        # We try to connect a client first, if it fails the backend will not start
        # It avoid potential issue when we launch the channel event hub in a subprocess
        with get_hfc() as (loop, client):
            logger.info('Start the event application.')

        p1 = multiprocessing.Process(target=wait)
        p1.start()

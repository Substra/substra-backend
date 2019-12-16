import asyncio
import json
import logging
import multiprocessing
import os
import time
import contextlib

from django.apps import AppConfig

from django.conf import settings

import glob

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.util.keyvaluestore import FileKeyValueStore

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


def tuple_get_worker(tuple_type, _tuple):
    if tuple_type == 'aggregatetuple':
        return _tuple['worker']
    return _tuple['dataset']['worker']


def on_tuples(cc_event, block_number, tx_id, tx_status):
    payload = json.loads(cc_event['payload'])
    owner = get_owner()
    worker_queue = f"{LEDGER['name']}.worker"

    for tuple_type, _tuples in payload.items():
        if not _tuples:
            continue

        for _tuple in _tuples:
            key = _tuple['key']
            status = _tuple['status']

            if tx_status != 'VALID':
                logger.error(
                    f'Failed transaction on task {key}: type={tuple_type}'
                    f' status={status} with tx status: {tx_status}')
                continue
            logger.info(f'Processing task {key}: type={tuple_type} status={status}')

            if status != 'todo':
                continue

            if tuple_type is None:
                continue

            tuple_owner = tuple_get_worker(tuple_type, _tuple)
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

        peer_port = peer["port"][os.environ.get('BACKEND_PEER_PORT', 'external')]

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
        while True:
            try:
                with get_hfc() as (loop, client):
                    logger.info('Start the event application.')
            except Exception as e:
                logger.exception(e)
                time.sleep(5)
                logger.info('Retry to connect the event application to the ledger')
            else:
                break

        p1 = multiprocessing.Process(target=wait)
        p1.start()

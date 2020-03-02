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

from substrapp.tasks.tasks import prepare_tuple, on_compute_plan
from substrapp.utils import get_owner
from substrapp.ledger_utils import get_hfc

from celery.result import AsyncResult

from grpc import RpcError


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


def tuple_get_worker(event_type, asset):
    if event_type == 'aggregatetuple':
        return asset['worker']
    return asset['dataset']['worker']


def on_tuples_event(tx_status, event_type, asset):

    owner = get_owner()
    worker_queue = f"{LEDGER['name']}.worker"

    key = asset['key']
    status = asset['status']

    if tx_status != 'VALID':
        logger.error(
            f'Failed transaction on task {key}: type={event_type}'
            f' status={status} with tx status: {tx_status}')
        return

    logger.info(f'Processing task {key}: type={event_type} status={status}')

    if status != 'todo':
        return

    if event_type is None:
        return

    tuple_owner = tuple_get_worker(event_type, asset)

    if tuple_owner != owner:
        logger.debug(f'Skipping task {key}: owner does not match'
                     f' ({tuple_owner} vs {owner})')
        return

    if AsyncResult(key).state != 'PENDING':
        logger.info(f'Skipping task {key}: already exists')
        return

    prepare_tuple.apply_async(
        (asset, event_type),
        task_id=key,
        queue=worker_queue
    )


def on_compute_plan_event(tx_status, asset):

    worker_queue = f"{LEDGER['name']}.worker"

    key = asset['computePlanID']

    # Currently, we received this event on done, failed and canceled status
    # We apply the same behavior for those three status.
    # In the future, we can apply a conditional strategy based on the status.
    status = asset['status']

    if tx_status != 'VALID':
        logger.error(
            f'Failed transaction on cleaning task {key}: type=computePlan'
            f' status={status} with tx status: {tx_status}')
        return

    logger.info(f'Processing cleaning task {key}: type=computePlan status={status}')

    on_compute_plan.apply_async(
        (asset, ),
        task_id=key,
        queue=worker_queue
    )


def on_event(cc_event, block_number, tx_id, tx_status):
    payload = json.loads(cc_event['payload'])

    for event_type, assets in payload.items():

        if not assets:
            continue

        for asset in assets:

            if event_type == 'computePlan':
                on_compute_plan_event(tx_status, asset)
            else:
                on_tuples_event(tx_status, event_type, asset)


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

            # Note:
            #   We do a loop to connect to the channel event hub because grpc may disconnect and create an exception
            #   Since we're in a django app of backend, an exception here will not crash the server (if the "ready"
            #   method has already returned "true").
            #   It makes it difficult to reconnect automatically because we need to kill the server
            #   to trigger the connexion.
            #   So we catch this exception (RPC error) and retry to connect to the event loop.
            #   Ideally, we'd extract the event app from the backend project into a separate service/process.

            while True:
                # use chaincode event
                channel_event_hub = channel.newChannelEventHub(target_peer,
                                                               requestor)
                try:
                    # We want to replay blocks from the beginning (start=0) if channel event hub was disconnected during
                    # events emission
                    stream = channel_event_hub.connect(start=0,
                                                       filtered=False)

                    channel_event_hub.registerChaincodeEvent(chaincode_name,
                                                             'chaincode-updates',
                                                             onEvent=on_event)

                    logger.error(f'Connect to Channel Event Hub')
                    loop.run_until_complete(stream)

                except RpcError as e:
                    logger.error(f'Channel Event Hub failed ({type(e)}): {e} re-connecting in 5s')
                    time.sleep(5)


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
                logger.error('Retry to connect the event application to the ledger')
            else:
                break

        p1 = multiprocessing.Process(target=wait)
        p1.start()

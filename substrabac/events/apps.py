import asyncio
import contextlib
import json

from django.apps import AppConfig

from django.conf import settings

import glob

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.util.keyvaluestore import FileKeyValueStore

from substrapp.tasks import prepareTrainTuple

LEDGER = getattr(settings, 'LEDGER', None)

@contextlib.contextmanager
def get_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()


class EventsConfig(AppConfig):
    name = 'events'

    def onEvent(self, block):
        payload = json.loads(
            block['data']['data'][0]['payload']['data']['actions'][0]['payload']['action']['proposal_response_payload'][
                'extension']['events']['payload'])
        print(payload)
        worker_queue = f"{settings.LEDGER['name']}.worker"
        if payload['status'] == 'todo':
            prepareTrainTuple.apply_async((payload,), queue=worker_queue)

    def ready(self):
        with get_event_loop() as loop:
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
            stream = channel_event_hub.connect(unregister=False, filtered=False)
            cr = channel_event_hub.registerChaincodeEvent(chaincode_name, 'traintuple-creation', onEvent=self.onEvent)
            loop.run_until_complete(stream)



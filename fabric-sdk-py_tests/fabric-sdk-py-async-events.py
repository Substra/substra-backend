import os
import sys
import asyncio

from hfc.fabric import Client
from hfc.fabric.block_decoder import FilteredBlockDecoder
from hfc.util.crypto.crypto import ecies

from hfc.fabric.transaction.tx_context import TXContext
from hfc.fabric.transaction.tx_proposal_request import TXProposalRequest


dir_path = os.path.dirname(os.path.realpath(__file__))

async def main():
    cli = Client(net_profile=os.path.join(dir_path, '../network.json'))
    admin_owkin = cli.get_user('owkin', 'admin')

    cli.new_channel('mychannel')
    peer = cli.get_peer('peer1-owkin')

    events = cli.get_events(admin_owkin, peer, 'mychannel', start=0, filtered=True)

    async for v in cli.getEvents(events):
        print(v)



asyncio.run(main(), debug=True)


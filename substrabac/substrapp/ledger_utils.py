import asyncio
import json

from rest_framework import status
from django.conf import settings
from django.http import Http404

from substrapp.utils import JsonException

LEDGER = getattr(settings, 'LEDGER', None)
if LEDGER:
    asyncio.set_event_loop(LEDGER['hfc']['loop'])


# careful, passing invoke parameters to queryLedger will NOT fail
def queryLedger(fcn, args=None):

    if args is None:
        args = []

    peer = LEDGER['peer']
    loop = LEDGER['hfc']['loop']
    client = LEDGER['hfc']['client']
    requestor = LEDGER['hfc']['requestor']
    channel_name = LEDGER['channel_name']
    chaincode_name = LEDGER['chaincode_name']

    # Get chaincode version
    response = loop.run_until_complete(
        client.query_instantiated_chaincodes(
            requestor=requestor,
            channel_name=channel_name,
            peers=[peer['name']],
            decode=True
        ))
    for ccs in response:
        for cc in ccs.chaincodes:
            if cc.name == chaincode_name:
                chaincode_version = cc.version

    try:
        # Async - need loop
        response = loop.run_until_complete(
            client.chaincode_query(
                requestor=requestor,
                channel_name=channel_name,
                peers=[peer['name']],
                args=args,
                cc_name=chaincode_name,
                cc_version=chaincode_version,
                fcn=fcn))
    except Exception as e:
        st = status.HTTP_400_BAD_REQUEST
        data = {'message': str(e)}
    else:
        msg = f'Query of channel \'{channel_name}\' on the peer \'{peer["host"]}\' was successful\n'
        print(msg, flush=True)

        st = status.HTTP_200_OK

        # TO DO : review parsing error in case of failure
        #         May have changed by using fabric-sdk-py
        try:
            # json transformation if needed
            data = json.loads(response)
        except json.decoder.JSONDecodeError:
            st = status.HTTP_400_BAD_REQUEST

            if 'access denied' in response:
                st = status.HTTP_403_FORBIDDEN
            elif 'no element with key' in response:
                st = status.HTTP_404_NOT_FOUND

            data = {'message': response}

    # TODO: get 409 from the chaincode
    if 'message' in data and 'tkey' in data['message']:
        pkhash = data['message'].replace('(', '').replace(')', '').split('tkey: ')[-1].strip()

        if len(pkhash) == 64:
            st = status.HTTP_409_CONFLICT
            data['pkhash'] = pkhash

    return data, st


def getObjectFromLedger(pk, query):
    # get instance from remote node
    data, st = queryLedger(fcn=query, args=[f'{pk}'])

    if st == status.HTTP_404_NOT_FOUND:
        raise Http404('Not found')

    if st != status.HTTP_200_OK:
        raise JsonException(data)

    if 'permissions' not in data or data['permissions'] == 'all':
        return data
    else:
        raise Exception('Not Allowed')


def invokeLedger(fcn, args=None, cc_pattern=None, sync=False):

    if args is None:
        args = []

    peer = LEDGER['peer']
    loop = LEDGER['hfc']['loop']
    client = LEDGER['hfc']['client']
    requestor = LEDGER['hfc']['requestor']
    channel_name = LEDGER['channel_name']
    chaincode_name = LEDGER['chaincode_name']

    # Get chaincode version
    response = loop.run_until_complete(
        client.query_instantiated_chaincodes(
            requestor=requestor,
            channel_name=channel_name,
            peers=[peer['name']],
            decode=True
        ))
    for ccs in response:
        for cc in ccs.chaincodes:
            if cc.name == chaincode_name:
                chaincode_version = cc.version

    try:
        # Async - need loop
        kwargs = {
            'requestor': requestor,
            'channel_name': channel_name,
            'peers': [peer['name']],
            'args': args,
            'cc_name': chaincode_name,
            'cc_version': chaincode_version,
            'fcn': fcn,
            'wait_for_event': sync,
            'wait_for_event_timeout': 45
        }
        if cc_pattern:
            kwargs['cc_pattern'] = cc_pattern

        response = loop.run_until_complete(client.chaincode_invoke(**kwargs))
    except TimeoutError as e:
        st = status.HTTP_408_REQUEST_TIMEOUT
        data = {'message': str(e)}
    except Exception as e:
        st = status.HTTP_400_BAD_REQUEST
        data = {'message': str(e)}
    else:
        # TO DO : review parsing error in case of failure
        #         May have changed by using fabric-sdk-py
        # elif 'access denied' in msg or 'authentication handshake failed' in msg:
        #     st = status.HTTP_403_FORBIDDEN

        st = status.HTTP_201_CREATED
        try:
            response = json.loads(response)
            pkhash = response.get('key', response.get('keys'))
            data = {'pkhash': pkhash}
        except json.decoder.JSONDecodeError:
            st = status.HTTP_400_BAD_REQUEST
            data = {'message': response}

    # TODO: get 409 from the chaincode
    if 'message' in data and 'tkey' in data['message']:
        pkhash = data['message'].replace('(', '').replace(')', '').split('tkey: ')[-1].strip()
        if len(pkhash) == 64:
            st = status.HTTP_409_CONFLICT
            data['pkhash'] = pkhash

    return data, st

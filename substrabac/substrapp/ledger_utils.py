import asyncio
import json

from rest_framework import status
from django.conf import settings
from django.http import Http404

from substrapp.utils import JsonException

LEDGER = getattr(settings, 'LEDGER', None)
if LEDGER:
    asyncio.set_event_loop(LEDGER['hfc']['loop'])


# careful, passing invoke parameters to query_ledger will NOT fail
def query_ledger(fcn, args=None):

    if args is None:
        args = []
    else:
        args = [json.dumps(args)]

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

    if data is not None:
        # TODO: get 409 from the chaincode
        if 'message' in data and 'tkey' in data['message']:
            pkhash = data['message'].replace('(', '').replace(')', '').split('tkey: ')[-1].strip()

            if len(pkhash) == 64:
                st = status.HTTP_409_CONFLICT
                data['pkhash'] = pkhash

        if 'permissions' in data and data['permissions'] != 'all':
            raise Exception('Not Allowed')

    return data, st


def get_object_from_ledger(pk, query):
    # get instance from remote node
    data, st = query_ledger(fcn=query, args={'key': pk})

    if st == status.HTTP_404_NOT_FOUND:
        raise Http404('Not found')

    if st != status.HTTP_200_OK:
        raise JsonException(data)

    return data


def invoke_ledger(fcn, args=None, cc_pattern=None, sync=False):

    if args is None:
        args = []
    else:
        args = [json.dumps(args)]

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


def log_fail_tuple(tuple_type, tuple_key, err_msg):
    err_msg = str(err_msg).replace('"', "'").replace('\\', "").replace('\\n', "")[:200]

    fail_type = 'logFailTrain' if tuple_type == 'traintuple' else 'logFailTest'

    data, st = invoke_ledger(
        fcn=fail_type,
        args={
            'key': tuple_key,
            'log': err_msg,
        },
        sync=True)

    return data, st


def log_success_tuple(tuple_type, tuple_key, res):
    if tuple_type == 'traintuple':
        invoke_fcn = 'logSuccessTrain'
        invoke_args = {
            'key': tuple_key,
            'outModel': {
                'hash': f'{res["end_model_file_hash"]}',
                'storageAddress': f'{res["end_model_file"]}',
            },
            'perf': f'{res["global_perf"]}',
            'log': f'Train - {res["job_task_log"]};',
        }

    elif tuple_type == 'testtuple':
        invoke_fcn = 'logSuccessTest'
        invoke_args = {
            'key': tuple_key,
            'perf': f'{res["global_perf"]}',
            'log': f'Test - {res["job_task_log"]};',
        }

    else:
        raise NotImplementedError()

    data, st = invoke_ledger(fcn=invoke_fcn, args=invoke_args, sync=True)

    return data, st


def log_start_tuple(tuple_type, tuple_key):
    start_type = None

    if tuple_type == 'traintuple':
        start_type = 'logStartTrain'
    elif tuple_type == 'testtuple':
        start_type = 'logStartTest'
    else:
        raise NotImplementedError()

    data, st = invoke_ledger(
        fcn=start_type,
        args={'key': tuple_key},
        sync=True)

    return data, st


def query_tuples(tuple_type, data_owner):
    tuples, st = query_ledger(
        fcn="queryFilter",
        args={
            'indexName': f'{tuple_type}~worker~status',
            'attributes': f'{data_owner},todo'
        }
    )
    return tuples, st

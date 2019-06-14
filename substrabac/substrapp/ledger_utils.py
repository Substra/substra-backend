import json
import logging
import contextlib

from django.conf import settings
from rest_framework import status

LEDGER = getattr(settings, 'LEDGER', None)


class LedgerError(Exception):
    status = status.HTTP_400_BAD_REQUEST

    def __init__(self, msg):
        super(LedgerError, self).__init__()
        self.msg = msg


class LedgerConflict(LedgerError):

    status = status.HTTP_409_CONFLICT

    def __init__(self, msg, pkhash):
        super(LedgerConflict, self).__init__(msg)
        self.pkhash = pkhash


class LedgerTimeout(LedgerError):
    status = status.HTTP_408_REQUEST_TIMEOUT


class LedgerForbidden(LedgerError):
    status = status.HTTP_403_FORBIDDEN


class LedgerNotFound(LedgerError):
    status = status.HTTP_404_NOT_FOUND


class LedgerBadResponse(LedgerError):
    pass


@contextlib.contextmanager
def get_hfc():
    loop, client = LEDGER['hfc']()
    try:
        yield (loop, client)
    finally:
        loop.close()
        del client


def call_ledger(call_type, fcn, args=None, kwargs=None):

    with get_hfc() as (loop, client):
        if not args:
            args = []
        else:
            args = [json.dumps(args)]

        peer = LEDGER['peer']
        requestor = LEDGER['requestor']

        chaincode_calls = {
            'invoke': client.chaincode_invoke,
            'query': client.chaincode_query,
        }

        channel_name = LEDGER['channel_name']
        chaincode_name = LEDGER['chaincode_name']

        peers = {
            'invoke': client._peers.keys(),
            'query': [peer['name']],
        }

        params = {
            'requestor': requestor,
            'channel_name': channel_name,
            'peers': peers[call_type],
            'args': args,
            'cc_name': chaincode_name,
            'fcn': fcn
        }

        if kwargs is not None and isinstance(kwargs, dict):
            params.update(kwargs)

        try:
            response = loop.run_until_complete(chaincode_calls[call_type](**params))
        except TimeoutError as e:
            raise LedgerTimeout(str(e))
        except Exception as e:
            logging.exception(e)
            raise LedgerError(str(e))

        # Sanity check of the response:
        if 'access denied' in response:
            raise LedgerForbidden(f'Access denied for {(fcn, args)}')
        elif 'no element with key' in response:
            raise LedgerNotFound(f'No element founded for {(fcn, args)}')
        elif 'tkey' in response:
            pkhash = response.replace('(', '').replace(')', '').split('tkey: ')[-1].strip()
            if len(pkhash) == 64:
                raise LedgerConflict(msg='Asset conflict', pkhash=pkhash)
            else:
                raise LedgerBadResponse(response)

        # Deserialize the stringified json
        try:
            response = json.loads(response)
        except json.decoder.JSONDecodeError:
            raise LedgerBadResponse(response)

        # Check permissions
        if response and 'permissions' in response and response['permissions'] != 'all':
            raise LedgerForbidden('Not allowed')

        return response


def query_ledger(fcn, args=None):
    # careful, passing invoke parameters to query_ledger will NOT fail
    return call_ledger('query', fcn=fcn, args=args)


def invoke_ledger(fcn, args=None, cc_pattern=None, sync=False):
    params = {
        'wait_for_event': sync,
    }

    if sync:
        params['wait_for_event_timeout'] = 45

    if cc_pattern:
        params['cc_pattern'] = cc_pattern

    response = call_ledger('invoke', fcn=fcn, args=args, kwargs=params)

    return {'pkhash': response.get('key', response.get('keys'))}


def get_object_from_ledger(pk, query):
    return query_ledger(fcn=query, args={'key': pk})


def log_fail_tuple(tuple_type, tuple_key, err_msg):
    err_msg = str(err_msg).replace('"', "'").replace('\\', "").replace('\\n', "")[:200]

    fail_type = 'logFailTrain' if tuple_type == 'traintuple' else 'logFailTest'

    return invoke_ledger(
        fcn=fail_type,
        args={
            'key': tuple_key,
            'log': err_msg,
        },
        sync=True)


def log_success_tuple(tuple_type, tuple_key, res):
    if tuple_type == 'traintuple':
        invoke_fcn = 'logSuccessTrain'
        invoke_args = {
            'key': tuple_key,
            'outModel': {
                'hash': res["end_model_file_hash"],
                'storageAddress': res["end_model_file"],
            },
            'perf': float(res["global_perf"]),
            'log': f'Train - {res["job_task_log"]};',
        }

    elif tuple_type == 'testtuple':
        invoke_fcn = 'logSuccessTest'
        invoke_args = {
            'key': tuple_key,
            'perf': float(res["global_perf"]),
            'log': f'Test - {res["job_task_log"]};',
        }

    else:
        raise NotImplementedError()

    return invoke_ledger(fcn=invoke_fcn, args=invoke_args, sync=True)


def log_start_tuple(tuple_type, tuple_key):
    start_type = None

    if tuple_type == 'traintuple':
        start_type = 'logStartTrain'
    elif tuple_type == 'testtuple':
        start_type = 'logStartTest'
    else:
        raise NotImplementedError()

    try:
        invoke_ledger(
            fcn=start_type,
            args={'key': tuple_key},
            sync=True)
    except LedgerTimeout:
        pass


def query_tuples(tuple_type, data_owner):
    data = query_ledger(
        fcn="queryFilter",
        args={
            'indexName': f'{tuple_type}~worker~status',
            'attributes': f'{data_owner},todo'
        }
    )

    data = [] if data is None else data

    return data

import json
import logging
import contextlib

from django.conf import settings
from rest_framework import status

LEDGER = getattr(settings, 'LEDGER', None)


class LedgerError(Exception):
    status = status.HTTP_400_BAD_REQUEST

    def __init__(self, msg):
        super(LedgerError, self).__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg


class LedgerResponseError(LedgerError):

    @classmethod
    def from_response(cls, response):
        return LedgerResponseError(response.get("error"))


class LedgerConflict(LedgerResponseError):

    status = status.HTTP_409_CONFLICT

    def __init__(self, msg, pkhash):
        super(LedgerConflict, self).__init__(msg)
        self.pkhash = pkhash

    def __repr__(self):
        return self.msg

    @classmethod
    def from_response(cls, response):
        pkhash = response["error"].replace('(', '').replace(')', '').split('tkey: ')[-1].strip()
        return LedgerConflict(response.get("error"), pkhash=pkhash)


class LedgerTimeout(LedgerError):
    status = status.HTTP_408_REQUEST_TIMEOUT


class LedgerForbidden(LedgerResponseError):
    status = status.HTTP_403_FORBIDDEN


class LedgerNotFound(LedgerResponseError):
    status = status.HTTP_404_NOT_FOUND


class LedgerMVCCError(LedgerError):
    status = status.HTTP_412_PRECONDITION_FAILED


class LedgerBadResponse(LedgerResponseError):
    pass


class LedgerStatusError(LedgerError):
    pass


@contextlib.contextmanager
def get_hfc():
    loop, client = LEDGER['hfc']()
    try:
        yield (loop, client)
    finally:
        del client
        loop.close()


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
            if hasattr(e, 'details') and 'access denied' in e.details():
                raise LedgerForbidden(f'Access denied for {(fcn, args)}')

            logging.exception(e)
            raise LedgerError(str(e))

        # Deserialize the stringified json
        try:
            response = json.loads(response)
        except json.decoder.JSONDecodeError:

            if response == 'MVCC_READ_CONFLICT':
                raise LedgerMVCCError(response)
            elif 'cannot change status' in response:
                raise LedgerStatusError(response)
            else:
                raise LedgerBadResponse(response)

        status_to_exception = {
            status.HTTP_400_BAD_REQUEST: LedgerBadResponse,
            status.HTTP_403_FORBIDDEN: LedgerForbidden,
            status.HTTP_404_NOT_FOUND: LedgerNotFound,
            status.HTTP_409_CONFLICT: LedgerConflict,
        }
        if response and "error" in response:
            status_code = response.get("status", status.HTTP_500_INTERNAL_SERVER_ERROR)
            exception_class = status_to_exception.get(status_code, LedgerBadResponse)
            raise exception_class.from_response(response)
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

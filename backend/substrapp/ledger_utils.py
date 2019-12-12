import contextlib
import functools
import json
import logging
import time

from django.conf import settings
from rest_framework import status
from grpc import RpcError


LEDGER = getattr(settings, 'LEDGER', None)
logger = logging.getLogger(__name__)


class LedgerError(Exception):
    status = status.HTTP_400_BAD_REQUEST

    def __init__(self, msg):
        super(LedgerError, self).__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg


class LedgerTimeoutNotHandled(LedgerError):
    pass


class LedgerResponseError(LedgerError):

    @classmethod
    def from_response(cls, response):
        return LedgerResponseError(response['error'])


class LedgerConflict(LedgerResponseError):

    status = status.HTTP_409_CONFLICT

    def __init__(self, msg, pkhash):
        super(LedgerConflict, self).__init__(msg)
        self.pkhash = pkhash

    def __repr__(self):
        return self.msg

    @classmethod
    def from_response(cls, response):
        pkhash = response.get('key')
        if not pkhash:
            return LedgerBadResponse(response['error'])
        return LedgerConflict(response['error'], pkhash=pkhash)


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


STATUS_TO_EXCEPTION = {
    status.HTTP_400_BAD_REQUEST: LedgerBadResponse,
    status.HTTP_403_FORBIDDEN: LedgerForbidden,
    status.HTTP_404_NOT_FOUND: LedgerNotFound,
    status.HTTP_409_CONFLICT: LedgerConflict,
}


def retry_on_error(delay=1, nbtries=5, backoff=2, exceptions=None):
    exceptions = exceptions or []
    exceptions_to_retry = [LedgerMVCCError, LedgerBadResponse, RpcError]
    exceptions_to_retry.extend(exceptions)
    exceptions_to_retry = tuple(exceptions_to_retry)

    def _retry(fn):
        @functools.wraps(fn)
        def _wrapper(*args, **kwargs):
            if not getattr(settings, 'LEDGER_CALL_RETRY', True):
                return fn(*args, **kwargs)

            _delay = delay
            _nbtries = nbtries
            _backoff = backoff

            while True:
                try:
                    return fn(*args, **kwargs)
                except exceptions_to_retry as e:
                    _nbtries -= 1
                    if not nbtries:
                        raise
                    _delay *= _backoff
                    time.sleep(_delay)
                    logger.warning(f'Function {fn.__name__} failed ({type(e)}): {e} retrying in {_delay}s')

        return _wrapper
    return _retry


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

            for arg in e.args:
                if 'MVCC_READ_CONFLICT' in arg:
                    logger.error(f'MVCC read conflict for {(fcn, args)}')
                    raise LedgerMVCCError(arg) from e

            try:  # get first failed response from list of protobuf ProposalResponse
                response = [r for r in e.args[0] if r.response.status != 200][0].response.message
            except Exception:
                raise LedgerError(str(e))

        # Deserialize the stringified json
        try:
            response = json.loads(response)
        except json.decoder.JSONDecodeError:
            if 'cannot change status' in response:
                raise LedgerStatusError(response)
            else:
                raise LedgerBadResponse(response)

        if response and 'error' in response:
            status_code = response['status']
            exception_class = STATUS_TO_EXCEPTION.get(status_code, LedgerBadResponse)
            raise exception_class.from_response(response)

        return response


def _invoke_ledger(fcn, args=None, cc_pattern=None, sync=False, only_pkhash=True):
    params = {
        'wait_for_event': sync,
    }

    if sync:
        params['wait_for_event_timeout'] = 45

    if cc_pattern:
        params['cc_pattern'] = cc_pattern

    response = call_ledger('invoke', fcn=fcn, args=args, kwargs=params)

    if only_pkhash:
        return {'pkhash': response.get('key', response.get('keys'))}
    else:
        return response


@retry_on_error(exceptions=[LedgerTimeout])
def query_ledger(fcn, args=None):
    # careful, passing invoke parameters to query_ledger will NOT fail
    return call_ledger('query', fcn=fcn, args=args)


@retry_on_error(exceptions=[LedgerTimeout])
def invoke_ledger(*args, **kwargs):
    return _invoke_ledger(*args, **kwargs)


@retry_on_error()
def update_ledger(*args, **kwargs):
    return _invoke_ledger(*args, **kwargs)


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


def get_object_from_ledger(pk, query):
    return query_ledger(fcn=query, args={'key': pk})


def _wait_until_status_after_timeout(tuple_type, tuple_key, expected_status):
    query_fcns = {
        'traintuple': 'queryTraintuple',
        'testtuple': 'queryTesttuple',
        'compositeTraintuple': 'queryCompositeTraintuple',
        'aggregatetuple': 'queryAggregatetuple',
    }
    query_fcn = query_fcns[tuple_type]

    max_tries = getattr(settings, 'LEDGER_MAX_RETRY_TIMEOUT', 5)
    trie = 1
    backoff = 5

    while trie <= max_tries:
        # sleep first as this is executed right after a request raising a timeout error
        time.sleep(trie * backoff)

        tuple_ = query_ledger(fcn=query_fcn, args={'key': tuple_key})
        status = tuple_['status']
        if status == expected_status:
            return

        logger.error(
            f'{tuple_type} {tuple_key} wrong status {status}: expecting {expected_status} (trie {trie})'
        )
        trie += 1

    raise LedgerTimeoutNotHandled(
        f'{tuple_type} {tuple_key} wrong status {status}: expecting {expected_status}')


LOG_TUPLE_INVOKE_FCNS = {
    'doing': {
        'traintuple': 'logStartTrain',
        'testtuple': 'logStartTest',
        'compositeTraintuple': 'logStartCompositeTrain',
        'aggregatetuple': 'logStartAggregate',
    },
    'done': {
        'traintuple': 'logSuccessTrain',
        'testtuple': 'logSuccessTest',
        'compositeTraintuple': 'logSuccessCompositeTrain',
        'aggregatetuple': 'logSuccessAggregate',
    },
    'failed': {
        'traintuple': 'logFailTrain',
        'testtuple': 'logFailTest',
        'compositeTraintuple': 'logFailCompositeTrain',
        'aggregatetuple': 'logFailAggregate',
    },
}


def _update_tuple_status(tuple_type, tuple_key, status, extra_kwargs=None):
    """Update tuple status to doing, done or failed.

    In case of ledger timeout, query the ledger until the status has been updated.
    """
    try:
        invoke_fcn = LOG_TUPLE_INVOKE_FCNS[status][tuple_type]
    except KeyError:
        raise NotImplementedError(f'Missing method for {tuple_type} status {status}')

    invoke_args = {
        'key': tuple_key,
    }
    if extra_kwargs:
        invoke_args.update(extra_kwargs)

    try:
        update_ledger(fcn=invoke_fcn, args=invoke_args, sync=True)
    except LedgerTimeout:
        _wait_until_status_after_timeout(tuple_type, tuple_key, status)


def log_start_tuple(tuple_type, tuple_key):
    _update_tuple_status(tuple_type, tuple_key, 'doing')


def log_fail_tuple(tuple_type, tuple_key, err_msg):
    err_msg = str(err_msg).replace('"', "'").replace('\\', "").replace('\\n', "")[:200]
    extra_kwargs = {
        'log': err_msg,
    }
    _update_tuple_status(tuple_type, tuple_key, 'failed', extra_kwargs=extra_kwargs)


def log_success_tuple(tuple_type, tuple_key, res):
    extra_kwargs = {
        'log': '',
    }

    if tuple_type in ('traintuple', 'aggregatetuple'):
        extra_kwargs.update({
            'outModel': {
                'hash': res["end_model_file_hash"],
                'storageAddress': res["end_model_file"],
            },
        })

    elif tuple_type == 'compositeTraintuple':
        extra_kwargs.update({
            'outHeadModel': {
                'hash': res["end_head_model_file_hash"],
                'storageAddress': res["end_head_model_file"],
            },
            'outTrunkModel': {
                'hash': res["end_trunk_model_file_hash"],
                'storageAddress': res["end_trunk_model_file"],
            },
        })

    elif tuple_type == 'testtuple':
        extra_kwargs.update({
            'perf': float(res["global_perf"]),
        })

    _update_tuple_status(tuple_type, tuple_key, 'done', extra_kwargs=extra_kwargs)

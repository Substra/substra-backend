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
    """Base error from ledger."""
    # FIXME the base error status code should be 500, the chaincode is currently
    #       responding with 500 status code for some 400 errors
    status = status.HTTP_400_BAD_REQUEST  # status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg

    @classmethod
    def from_response_dict(cls, response):
        return cls(response['error'])


class LedgerStatusError(LedgerError):
    """Could not update tuple status error."""
    pass


class LedgerInvalidResponse(LedgerError):
    """Could not parse ledger response."""
    pass


class LedgerTimeout(LedgerError):
    """Ledger does not respond in time."""
    status = status.HTTP_408_REQUEST_TIMEOUT


class LedgerMVCCError(LedgerError):
    status = status.HTTP_412_PRECONDITION_FAILED


class LedgerPhantomReadConflictError(LedgerError):
    status = status.HTTP_412_PRECONDITION_FAILED


class LedgerEndorsementPolicyFailure(LedgerError):
    status = status.HTTP_412_PRECONDITION_FAILED


class LedgerUnavailable(LedgerError):
    """Ledger is not available."""
    status = status.HTTP_503_SERVICE_UNAVAILABLE


class LedgerBadRequest(LedgerError):
    """Invalid request."""
    status = status.HTTP_400_BAD_REQUEST


class LedgerConflict(LedgerError):
    """Asset already exists."""
    status = status.HTTP_409_CONFLICT

    def __init__(self, msg, pkhash):
        super().__init__(msg)
        self.pkhash = pkhash

    @classmethod
    def from_response_dict(cls, response):
        pkhash = response.get('key')
        if not pkhash:
            return LedgerError(response['error'])
        return cls(response['error'], pkhash=pkhash)


class LedgerNotFound(LedgerError):
    """Asset not found."""
    status = status.HTTP_404_NOT_FOUND


class LedgerForbidden(LedgerError):
    """Organisation is not allowed to perform the operation."""
    status = status.HTTP_403_FORBIDDEN


_STATUS_TO_EXCEPTION = {
    status.HTTP_400_BAD_REQUEST: LedgerBadRequest,
    status.HTTP_403_FORBIDDEN: LedgerForbidden,
    status.HTTP_404_NOT_FOUND: LedgerNotFound,
    status.HTTP_409_CONFLICT: LedgerConflict,
}


def _raise_for_status(response):
    """Parse ledger response and raise exceptions in case of errors."""
    if not response or 'error' not in response:
        return

    if 'cannot change status' in response['error']:
        raise LedgerStatusError.from_response_dict(response)

    status_code = response['status']
    exception_class = _STATUS_TO_EXCEPTION.get(status_code, LedgerError)

    raise exception_class.from_response_dict(response)


def retry_on_error(delay=1, nbtries=15, backoff=2, exceptions=None):
    exceptions = exceptions or []
    exceptions_to_retry = [
        LedgerMVCCError,
        LedgerInvalidResponse,
        RpcError,
        LedgerUnavailable,
        LedgerPhantomReadConflictError,
        LedgerEndorsementPolicyFailure,
        # Retry on LedgerStatusError because of potential ledger state difference
        # caused by not synchronous committed block receipt between nodes.
        LedgerStatusError,
    ]
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
                    _delay += _backoff
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
        loop.run_until_complete(
            client.close_grpc_channels()
        )
        del client
        loop.close()


def _get_endorsing_peers(strategy, current_peer, all_peers):
    if strategy == 'SELF':
        return [current_peer]
    if strategy == 'ALL':
        return all_peers

    raise Exception(f'strategy should either be "SELF" or "ALL", "{strategy}" given')


def get_invoke_endorsing_peers(current_peer, all_peers):
    return _get_endorsing_peers(
        strategy=settings.LEDGER_INVOKE_STRATEGY,
        current_peer=current_peer,
        all_peers=all_peers
    )


def get_query_endorsing_peers(current_peer, all_peers):
    return _get_endorsing_peers(
        strategy=settings.LEDGER_QUERY_STRATEGY,
        current_peer=current_peer,
        all_peers=all_peers
    )


def _call_ledger(call_type, fcn, args=None, kwargs=None):

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

        all_peers = client._peers.keys()
        current_peer = peer['name']

        peers = {
            'invoke': get_invoke_endorsing_peers(current_peer=current_peer, all_peers=all_peers),
            'query': get_query_endorsing_peers(current_peer=current_peer, all_peers=all_peers),
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
            # TODO add a method to parse properly the base Exception raised by the fabric-sdk-py
            if hasattr(e, 'details') and 'access denied' in e.details():
                raise LedgerForbidden(f'Access denied for {(fcn, args)}')

            if hasattr(e, 'details') and 'failed to connect to all addresses' in e.details():
                logger.error(f'failed to reach all peers {all_peers}, current_peer is {current_peer}')
                raise LedgerUnavailable(f'Failed to connect to all addresses for {(fcn, args)}')

            for arg in e.args:
                if 'MVCC_READ_CONFLICT' in arg:
                    logger.error(f'MVCC read conflict for {(fcn, args)}')
                    raise LedgerMVCCError(arg) from e

                if 'PHANTOM_READ_CONFLICT' in arg:
                    logger.error(f'PHANTOM read conflict for {(fcn, args)}')
                    raise LedgerPhantomReadConflictError(arg) from e

                if 'ENDORSEMENT_POLICY_FAILURE' in arg:
                    logger.error(f'ENDORSEMENT_POLICY_FAILURE for {(fcn, args)}')
                    raise LedgerEndorsementPolicyFailure(arg) from e

            try:  # get first failed response from list of protobuf ProposalResponse
                response = [r for r in e.args[0] if r.response.status != 200][0].response.message
            except Exception:
                raise LedgerError(str(e))

        # Deserialize the stringified json
        try:
            response = json.loads(response)
        except json.decoder.JSONDecodeError:
            raise LedgerInvalidResponse(response)

        # Raise errors if status is not ok
        _raise_for_status(response)

        return response


def call_ledger(call_type, fcn, *args, **kwargs):
    """Call ledger and log each request."""
    ts = time.time()
    error = None
    try:
        return _call_ledger(call_type, fcn, *args, **kwargs)
    except Exception as e:
        error = e.__class__.__name__
        raise
    finally:
        # add a log even if the function raises an exception
        te = time.time()
        elaps = (te - ts) * 1000
        logger.info(f'smartcontract {call_type}:{fcn}; elaps={elaps:.2f}ms; error={error}')


def _invoke_ledger(fcn, args=None, cc_pattern=None, sync=False, only_pkhash=True):
    params = {
        'wait_for_event': sync,
        'grpc_broker_unavailable_retry': 5,
        'grpc_broker_unavailable_retry_delay': 3000,
        'raise_broker_unavailable': False
    }

    if sync:
        params['wait_for_event_timeout'] = settings.LEDGER_WAIT_FOR_EVENT_TIMEOUT

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


@retry_on_error()
def invoke_ledger(*args, **kwargs):
    return _invoke_ledger(*args, **kwargs)


@retry_on_error(exceptions=[LedgerTimeout])
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

    update_ledger(fcn=invoke_fcn, args=invoke_args, sync=True)


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

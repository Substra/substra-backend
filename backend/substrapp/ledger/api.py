import functools
import json
import logging
import time

from uuid import UUID
from django.conf import settings
from grpc import RpcError
from substrapp.ledger.connection import get_hfc
from substrapp.ledger.exceptions import (raise_for_status, LedgerForbidden, LedgerTimeout, LedgerMVCCError,
                                         LedgerInvalidResponse, LedgerUnavailable, LedgerPhantomReadConflictError,
                                         LedgerEndorsementPolicyFailure, LedgerStatusError, LedgerError)

logger = logging.getLogger(__name__)


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
            if not settings.LEDGER_CALL_RETRY:
                return fn(*args, **kwargs)

            _delay = delay
            _nbtries = nbtries
            _backoff = backoff

            while True:
                try:
                    return fn(*args, **kwargs)
                except exceptions_to_retry as e:
                    _nbtries -= 1
                    if not _nbtries:
                        raise
                    _delay += _backoff
                    time.sleep(_delay)
                    logger.warning(f'Function {fn.__name__} failed ({type(e)}): {e} retrying in {_delay}s')

        return _wrapper
    return _retry


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

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def _call_ledger(channel_name, call_type, fcn, args=None, kwargs=None):

    with get_hfc(channel_name) as (loop, client, user):
        if not args:
            args = []
        else:
            args = [json.dumps(args, cls=UUIDEncoder)]

        chaincode_calls = {
            'invoke': client.chaincode_invoke,
            'query': client.chaincode_query,
        }

        all_peers = client._peers.keys()

        peers = {
            'invoke': get_invoke_endorsing_peers(current_peer=settings.LEDGER_PEER_NAME, all_peers=all_peers),
            'query': get_query_endorsing_peers(current_peer=settings.LEDGER_PEER_NAME, all_peers=all_peers),
        }

        params = {
            'requestor': user,
            'channel_name': channel_name,
            'peers': peers[call_type],
            'args': args,
            'cc_name': settings.LEDGER_CHAINCODE_NAME,
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
                logger.error(f'failed to reach all peers {all_peers}, current_peer is {settings.LEDGER_PEER_NAME}')
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
        raise_for_status(response)

        return response


def call_ledger(channel_name, call_type, fcn, *args, **kwargs):
    """Call ledger and log each request."""
    ts = time.time()
    error = None
    try:
        return _call_ledger(channel_name, call_type, fcn, *args, **kwargs)
    except Exception as e:
        error = e.__class__.__name__
        raise
    finally:
        # add a log even if the function raises an exception
        te = time.time()
        elaps = (te - ts) * 1000
        if error is None:
            logger.info(f"(smartcontract) {call_type}:{fcn} took {elaps:.2f} ms")
        else:
            logger.info(f"(smartcontract) {call_type}:{fcn} took {elaps:.2f} ms. Error: {error}")


def _invoke_ledger(channel_name, fcn, args=None, cc_pattern=None, sync=False, only_pkhash=True):
    params = {
        'wait_for_event': sync,
        'grpc_broker_unavailable_retry': 5,
        'grpc_broker_unavailable_retry_delay': 3000,
        'raise_broker_unavailable': False
    }

    if sync:
        params['wait_for_event_timeout'] = settings.LEDGER_WAIT_FOR_EVENT_TIMEOUT_SECONDS

    if cc_pattern:
        params['cc_pattern'] = cc_pattern

    response = call_ledger(channel_name, 'invoke', fcn=fcn, args=args, kwargs=params)

    if only_pkhash:
        return {'pkhash': response.get('key', response.get('keys'))}
    else:
        return response


@retry_on_error(exceptions=[LedgerTimeout])
def query_ledger(channel_name, fcn, args=None):
    # careful, passing invoke parameters to query_ledger will NOT fail
    return call_ledger(channel_name, 'query', fcn=fcn, args=args)


@retry_on_error()
def invoke_ledger(channel_name, *args, **kwargs):
    return _invoke_ledger(channel_name, *args, **kwargs)


@retry_on_error(exceptions=[LedgerTimeout])
def update_ledger(channel_name, *args, **kwargs):
    return _invoke_ledger(channel_name, *args, **kwargs)


def query_tuples(channel_name, tuple_type, data_owner):
    # Convert to chaincode index for compositeTraintuple
    tuple_type = 'compositeTraintuple' if tuple_type == 'composite_traintuple' else tuple_type
    data = query_ledger(
        channel_name,
        fcn="queryFilter",
        args={
            'indexName': f'{tuple_type}~worker~status',
            'attributes': f'{data_owner},todo'
        }
    )

    data = [] if data is None else data

    return data


def get_object_from_ledger(channel_name, pk, query):
    return query_ledger(channel_name, fcn=query, args={'key': pk})


LOG_TUPLE_INVOKE_FCNS = {
    'doing': {
        'traintuple': 'logStartTrain',
        'testtuple': 'logStartTest',
        'composite_traintuple': 'logStartCompositeTrain',
        'aggregatetuple': 'logStartAggregate',
    },
    'done': {
        'traintuple': 'logSuccessTrain',
        'testtuple': 'logSuccessTest',
        'composite_traintuple': 'logSuccessCompositeTrain',
        'aggregatetuple': 'logSuccessAggregate',
    },
    'failed': {
        'traintuple': 'logFailTrain',
        'testtuple': 'logFailTest',
        'composite_traintuple': 'logFailCompositeTrain',
        'aggregatetuple': 'logFailAggregate',
    },
}


def _update_tuple_status(channel_name, tuple_type, tuple_key, status, extra_kwargs=None):
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

    update_ledger(channel_name, fcn=invoke_fcn, args=invoke_args, sync=True)


def log_start_tuple(channel_name, tuple_type, tuple_key):
    _update_tuple_status(channel_name, tuple_type, tuple_key, 'doing')


def log_fail_tuple(channel_name, tuple_type, tuple_key, err_msg):
    err_msg = str(err_msg).replace('"', "'").replace('\\', "").replace('\\n', "")[:200]
    extra_kwargs = {
        'log': err_msg,
    }
    _update_tuple_status(channel_name, tuple_type, tuple_key, 'failed', extra_kwargs=extra_kwargs)


def log_success_tuple(channel_name, tuple_type, tuple_key, res):
    extra_kwargs = {
        'log': '',
    }

    if tuple_type in ('traintuple', 'aggregatetuple'):
        extra_kwargs.update({
            'out_model': {
                'key': res["end_model_key"],
                'hash': res["end_model_checksum"],
                'storage_address': res["end_model_storage_address"],
            },
        })

    elif tuple_type == 'composite_traintuple':
        extra_kwargs.update({
            'out_head_model': {
                'key': res["end_head_model_key"],
                'hash': res["end_head_model_checksum"],
            },
            'out_trunk_model': {
                'key': res["end_trunk_model_key"],
                'hash': res["end_trunk_model_checksum"],
                'storage_address': res["end_trunk_model_storage_address"],
            },
        })

    elif tuple_type == 'testtuple':
        extra_kwargs.update({
            'perf': float(res["global_perf"]),
        })

    _update_tuple_status(channel_name, tuple_type, tuple_key, 'done', extra_kwargs=extra_kwargs)

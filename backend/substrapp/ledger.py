from __future__ import absolute_import, unicode_literals

from celery import shared_task
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from substrapp import models
from substrapp.ledger_utils import invoke_ledger, LedgerError, LedgerTimeout


_MESSAGE = (
    'The substra network has been notified for adding/updating this asset. '
    'Please be aware you won\'t get return values from the ledger. '
    'You will need to check manually'
)


def __create_db_asset(model, fcn, args, key, sync=False):
    try:
        instance = model.objects.get(pk=key)
    except ObjectDoesNotExist:
        instance = None

    try:
        data = invoke_ledger(fcn=fcn, args=args, sync=sync)
    except LedgerTimeout:
        # LedgerTimeout herits from LedgerError do not delete
        # In case of timeout we keep the instance if it exists
        raise
    except LedgerError:
        # if not created on ledger, delete from local db
        if instance:
            instance.delete()
        raise

    if instance:
        instance.validated = True
        instance.save()
        data['validated'] = True

    return data


def _create_db_asset(fcn, model, args, key):
    if getattr(settings, 'LEDGER_SYNC_ENABLED', True):
        return __create_db_asset(model, fcn, args, key, sync=True)
    else:
        shared_task(__create_db_asset)(model, fcn, args, key, sync=False)
        return {'message': _MESSAGE}


def __create_db_assets(model, fcn, args, keys, sync=False):
    try:
        instances = model.objects.filter(pk__in=keys)
    except ObjectDoesNotExist:
        instances = None

    try:
        data = invoke_ledger(fcn=fcn, args=args, sync=sync)
    except LedgerTimeout:
        # LedgerTimeout herits from LedgerError do not delete
        # In case of timeout we keep the instances if it exists
        raise
    except LedgerError:
        # if not created on ledger, delete from local db
        if instances:
            instances.delete()
        raise

    if instances:
        instances.update(validated=True)
        data['validated'] = True

    return data


def _create_db_assets(fcn, model, args, keys):
    if getattr(settings, 'LEDGER_SYNC_ENABLED', True):
        return __create_db_assets(model, fcn, args, keys, sync=True)
    else:
        shared_task(__create_db_asset)(model, fcn, args, keys, sync=False)
        return {'message': _MESSAGE}


def __create_asset(fcn, args, sync=False, **extra_kwargs):
    # create a wrapper as it seems the shared_task decorator from celery is not
    # compatible with our retry decorator on the invoke_ledger function
    return invoke_ledger(fcn=fcn, args=args, sync=sync, **extra_kwargs)


def _create_asset(fcn, args, **extra_kwargs):
    if getattr(settings, 'LEDGER_SYNC_ENABLED', True):
        return __create_asset(fcn, args=args, sync=True, **extra_kwargs)
    else:
        shared_task(__create_asset)(fcn, args=args, sync=False, **extra_kwargs)
        return {'message': _MESSAGE}


def create_traintuple(args):
    return _create_asset('createTraintuple', args)


def create_testtuple(args):
    return _create_asset('createTesttuple', args)


def create_aggregatetuple(args):
    return _create_asset('createAggregatetuple', args)


def create_compositetraintuple(args):
    return _create_asset('createCompositeTraintuple', args)


def create_computeplan(args):
    return _create_asset('createComputePlan', args, only_pkhash=False)


def create_algo(args, key):
    return _create_db_asset('registerAlgo', models.Algo, args, key)


def create_aggregatealgo(args, key):
    return _create_db_asset('registerAggregateAlgo', models.AggregateAlgo, args, key)


def create_compositealgo(args, key):
    return _create_db_asset('registerCompositeAlgo', models.CompositeAlgo, args, key)


def create_datamanager(args, key):
    return _create_db_asset('registerDataManager', models.DataManager, args, key)


def create_datasamples(args, keys):
    return _create_db_assets('registerDataSample', models.DataSample, args, keys)


def create_objective(args, key):
    return _create_db_asset('registerObjective', models.Objective, args, key)


def update_datamanager(args):
    return _create_asset('updateDataManager', args=args)


def update_datasample(args):
    return _create_asset('updateDataSample', args=args)


def update_computeplan(args):
    return _create_asset('updateComputePlan', args, only_pkhash=False)

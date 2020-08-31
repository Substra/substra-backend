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


def __create_db_asset(channel_name, model, fcn, args, key, sync=False):
    try:
        instance = model.objects.get(pk=key)
    except ObjectDoesNotExist:
        instance = None

    try:
        data = invoke_ledger(channel_name, fcn=fcn, args=args, sync=sync)
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


def _create_db_asset(channel_name, fcn, model, args, key):
    if getattr(settings, 'LEDGER_SYNC_ENABLED', True):
        return __create_db_asset(channel_name, model, fcn, args, key, sync=True)
    else:
        shared_task(__create_db_asset)(channel_name, model, fcn, args, key, sync=False)
        return {'message': _MESSAGE}


def __create_db_assets(channel_name, model, fcn, args, keys, sync=False):
    try:
        instances = model.objects.filter(pk__in=keys)
    except ObjectDoesNotExist:
        instances = None

    try:
        data = invoke_ledger(channel_name, fcn=fcn, args=args, sync=sync)
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


def _create_db_assets(channel_name, fcn, model, args, keys):
    if getattr(settings, 'LEDGER_SYNC_ENABLED', True):
        return __create_db_assets(channel_name, model, fcn, args, keys, sync=True)
    else:
        shared_task(__create_db_asset)(channel_name, model, fcn, args, keys, sync=False)
        return {'message': _MESSAGE}


def __create_asset(channel_name, fcn, args, sync=False, **extra_kwargs):
    # create a wrapper as it seems the shared_task decorator from celery is not
    # compatible with our retry decorator on the invoke_ledger function
    return invoke_ledger(channel_name, fcn=fcn, args=args, sync=sync, **extra_kwargs)


def _create_asset(channel_name, fcn, args, **extra_kwargs):
    if getattr(settings, 'LEDGER_SYNC_ENABLED', True):
        return __create_asset(channel_name, fcn, args=args, sync=True, **extra_kwargs)
    else:
        shared_task(__create_asset)(channel_name, fcn, args=args, sync=False, **extra_kwargs)
        return {'message': _MESSAGE}


def create_traintuple(channel_name, args):
    return _create_asset(channel_name, 'createTraintuple', args)


def create_testtuple(channel_name, args):
    return _create_asset(channel_name, 'createTesttuple', args)


def create_aggregatetuple(channel_name, args):
    return _create_asset(channel_name, 'createAggregatetuple', args)


def create_compositetraintuple(channel_name, args):
    return _create_asset(channel_name, 'createCompositeTraintuple', args)


def create_computeplan(channel_name, args):
    return _create_asset(channel_name, 'createComputePlan', args, only_pkhash=False)


def create_algo(channel_name, args, key):
    return _create_db_asset(channel_name, 'registerAlgo', models.Algo, args, key)


def create_aggregatealgo(channel_name, args, key):
    return _create_db_asset(channel_name, 'registerAggregateAlgo', models.AggregateAlgo, args, key)


def create_compositealgo(channel_name, args, key):
    return _create_db_asset(channel_name, 'registerCompositeAlgo', models.CompositeAlgo, args, key)


def create_datamanager(channel_name, args, key):
    return _create_db_asset(channel_name, 'registerDataManager', models.DataManager, args, key)


def create_datasamples(channel_name, args, keys):
    return _create_db_assets(channel_name, 'registerDataSample', models.DataSample, args, keys)


def create_objective(channel_name, args, key):
    return _create_db_asset(channel_name, 'registerObjective', models.Objective, args, key)


def update_datamanager(channel_name, args):
    return _create_asset(channel_name, 'updateDataManager', args=args)


def update_datasample(channel_name, args):
    return _create_asset(channel_name, 'updateDataSample', args=args)


def update_computeplan(channel_name, args):
    return _create_asset(channel_name, 'updateComputePlan', args, only_pkhash=False)

from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from substrapp.ledger_utils import invoke_ledger, LedgerError, LedgerTimeout


class PermissionsSerializer(serializers.Serializer):
    public = serializers.BooleanField()
    authorized_ids = serializers.ListField(child=serializers.CharField())


def create_ledger_asset(model, fcn, args, pkhash, sync=False):
    try:
        instance = model.objects.get(pk=pkhash)
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


def create_ledger_assets(model, fcn, args, pkhashes, sync=False):
    try:
        instances = model.objects.filter(pk__in=pkhashes)
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

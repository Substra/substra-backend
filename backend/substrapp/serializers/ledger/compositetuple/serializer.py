from rest_framework import serializers

from django.conf import settings

from .util import createLedgerCompositetuple
from .tasks import createLedgerCompositetupleAsync

from substrapp.serializers.ledger.utils import PermissionsSerializer


class LedgerCompositeTupleSerializer(serializers.Serializer):
    algo_key = serializers.CharField(min_length=64, max_length=64)
    data_manager_key = serializers.CharField(min_length=64, max_length=64)
    objective_key = serializers.CharField(min_length=64, max_length=64)
    rank = serializers.IntegerField(allow_null=True, required=False, default=0)
    compute_plan_id = serializers.CharField(min_length=64, max_length=64, allow_blank=True, required=False)
    in_head_model_key = serializers.CharField(min_length=64, max_length=64)
    in_head_model_permissions = PermissionsSerializer()
    in_trunk_model_key = serializers.CharField(min_length=64, max_length=64)
    in_trunk_model_permissions = PermissionsSerializer()
    train_data_sample_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                                   min_length=1)
    tag = serializers.CharField(min_length=0, max_length=64, allow_blank=True, required=False)

    def get_args(self, validated_data):
        algo_key = validated_data.get('algo_key')
        data_manager_key = validated_data.get('data_manager_key')
        objective_key = validated_data.get('objective_key')
        rank = validated_data.get('rank', '')
        rank = '' if rank is None else str(rank)
        compute_plan_id = validated_data.get('compute_plan_id', '')
        train_data_sample_keys = validated_data.get('train_data_sample_keys', [])
        in_head_model_key = validated_data.get('in_head_model_key')
        in_head_model_permissions = validated_data.get('in_head_model_permissions')
        in_trunk_model_key = validated_data.get('in_trunk_model_key')
        in_trunk_model_permissions = validated_data.get('in_trunk_model_permissions')
        tag = validated_data.get('tag', '')

        args = {
            'algoKey': algo_key,
            'objectiveKey': objective_key,
            'inHeadModel': {
                'key': in_head_model_key,
                'permissions': {'process': {
                    'public': in_head_model_permissions.get('public'),
                    'authorizedIDs': in_head_model_permissions.get('authorized_ids'),
                }}
            },
            'inTrunkModel': {
                'key': in_trunk_model_key,
                'permissions': {'process': {
                    'public': in_trunk_model_permissions.get('public'),
                    'authorizedIDs': in_trunk_model_permissions.get('authorized_ids'),
                }}
            },
            'dataManagerKey': data_manager_key,
            'dataSampleKeys': train_data_sample_keys,
            'computePlanID': compute_plan_id,
            'rank': rank,
            'tag': tag
        }

        return args

    def create(self, validated_data):
        args = self.get_args(validated_data)

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            data = createLedgerCompositetuple(args, sync=True)
        else:
            # use a celery task, as we are in an http request transaction
            createLedgerCompositetupleAsync.delay(args)
            data = {
                'message': 'The substra network has been notified for adding this Compositetuple. '
                           'Please be aware you won\'t get return values from the ledger.'
                           'You will need to check manually'
            }

        return data

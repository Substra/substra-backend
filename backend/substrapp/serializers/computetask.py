from rest_framework import serializers
from rest_framework.fields import CharField, DictField, IntegerField

from substrapp.serializers.utils import PermissionsSerializer
from substrapp.orchestrator.api import get_orchestrator_client


class GenericComputeTaskSerializer(serializers.Serializer):
    key = serializers.UUIDField()
    category = IntegerField(min_value=0, max_value=4)
    algo_key = serializers.UUIDField()
    compute_plan_key = serializers.UUIDField(required=False, allow_null=True)
    metadata = DictField(child=CharField(), required=False, allow_null=True)
    parent_task_keys = serializers.ListField(child=serializers.UUIDField())
    tag = serializers.CharField(
        min_length=0,
        max_length=64,
        allow_blank=True,
        required=False,
        allow_null=True
    )

    def get_args(self, validated_data):
        # If the metadata or tag are set to None we want an empty variable of the correct type
        metadata = validated_data.get('metadata') or {}
        tag = validated_data.get('tag') or ''

        if metadata.get('__tag__'):
            raise Exception('"__tag__" cannot be used as a metadata key')

        metadata['__tag__'] = tag

        args = {
            'key': str(validated_data.get('key')),
            'category': validated_data.get('category'),
            'algo_key': str(validated_data.get('algo_key')),
            'compute_plan_key': str(validated_data.get('compute_plan_key')),
            'metadata': metadata,
            'parent_task_keys': list(set([str(p) for p in validated_data.get('parent_task_keys', [])])),
        }

        return args

    def create(self, channel_name, validated_data):
        args = self.get_args(validated_data)
        with get_orchestrator_client(channel_name) as client:
            return client.register_tasks({'tasks': [args]})


class OrchestratorCompositeTrainTaskSerializer(GenericComputeTaskSerializer):
    data_manager_key = serializers.UUIDField()
    data_sample_keys = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    trunk_permissions = PermissionsSerializer()

    def get_args(self, validated_data):
        args = super().get_args(validated_data)

        trunk_permissions = validated_data.get('trunk_permissions')
        args['composite'] = {
            'data_manager_key': str(validated_data.get('data_manager_key')),
            'data_sample_keys': [str(d) for d in validated_data.get('data_sample_keys')],
            'trunk_permissions': {
                'public': trunk_permissions.get('public'),
                'authorized_ids': trunk_permissions.get('authorized_ids'),
            }
        }

        return args


class OrchestratorTestTaskSerializer(GenericComputeTaskSerializer):
    data_manager_key = serializers.UUIDField(required=False, allow_null=True)
    objective_key = serializers.UUIDField(required=False)
    data_sample_keys = serializers.ListField(child=serializers.UUIDField(),
                                             min_length=0, required=False, allow_null=True)

    def get_args(self, validated_data):
        args = super().get_args(validated_data)

        datasample_keys = validated_data.get('data_sample_keys', []) or []
        datamanager_key = validated_data.get('data_manager_key', '') or ''

        args['test'] = {
            'objective_key': str(validated_data.get('objective_key')),
            'data_manager_key': str(datamanager_key),
            'data_sample_keys': [str(ds) for ds in datasample_keys],
        }

        return args


class OrchestratorTrainTaskSerializer(GenericComputeTaskSerializer):
    data_manager_key = serializers.UUIDField(required=False, allow_null=True)
    data_sample_keys = serializers.ListField(child=serializers.UUIDField(),
                                             min_length=0, required=False, allow_null=True)

    def get_args(self, validated_data):
        args = super().get_args(validated_data)

        args['train'] = {
            'data_manager_key': str(validated_data.get('data_manager_key')),
            'data_sample_keys': [str(ds) for ds in validated_data.get('data_sample_keys')],
        }

        return args


class OrchestratorAggregateTaskSerializer(GenericComputeTaskSerializer):
    worker = serializers.CharField()

    def get_args(self, validated_data):
        args = super().get_args(validated_data)

        args['aggregate'] = {
            'worker': validated_data.get('worker'),
        }

        return args

from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.fields import DictField
from rest_framework.reverse import reverse

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import DataManager
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers.utils import FileSizeValidator
from substrapp.serializers.utils import PermissionsSerializer
from substrapp.utils import get_hash


class DataManagerSerializer(DynamicFieldsModelSerializer):
    data_opener = serializers.FileField(validators=[FileSizeValidator()])
    description = serializers.FileField(validators=[FileSizeValidator()])

    class Meta:
        model = DataManager
        fields = "__all__"


class OrchestratorDataManagerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=30)
    permissions = PermissionsSerializer()
    metadata = DictField(child=CharField(), required=False, allow_null=True)
    logs_permission = PermissionsSerializer()

    def create(self, channel_name, validated_data):
        instance = self.initial_data.get("instance")
        name = validated_data.get("name")
        data_type = validated_data.get("type")
        permissions = validated_data.get("permissions")
        metadata = validated_data.get("metadata")
        logs_permission = validated_data.get("logs_permission")

        current_site = settings.DEFAULT_DOMAIN

        args = {
            "key": str(instance.key),
            "name": name,
            "opener": {
                "checksum": get_hash(instance.data_opener),
                "storage_address": current_site + reverse("substrapp:data_manager-opener", args=[instance.key]),
            },
            "type": data_type,
            "description": {
                "checksum": get_hash(instance.description),
                "storage_address": current_site + reverse("substrapp:data_manager-description", args=[instance.key]),
            },
            "new_permissions": {
                "public": permissions.get("public"),
                "authorized_ids": permissions.get("authorized_ids"),
            },
            "metadata": metadata,
            "logs_permission": {
                "public": logs_permission.get("public"),
                "authorized_ids": logs_permission.get("authorized_ids"),
            },
        }

        with get_orchestrator_client(channel_name) as client:
            return client.register_datamanager(args)

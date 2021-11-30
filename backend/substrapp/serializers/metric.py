from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.fields import DictField
from rest_framework.reverse import reverse

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Metric
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers.utils import FileSizeValidator
from substrapp.serializers.utils import FileValidator
from substrapp.serializers.utils import PermissionsSerializer
from substrapp.utils import get_hash


class MetricSerializer(DynamicFieldsModelSerializer):
    address = serializers.FileField(validators=[FileValidator(), FileSizeValidator()])

    class Meta:
        model = Metric
        fields = "__all__"


class OrchestratorMetricSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=100)
    permissions = PermissionsSerializer()
    metadata = DictField(child=CharField(), required=False, allow_null=True)

    def create(self, channel_name, validated_data):
        instance = self.initial_data.get("instance")
        name = validated_data.get("name")
        permissions = validated_data.get("permissions")
        metadata = validated_data.get("metadata")

        current_site = settings.DEFAULT_DOMAIN

        args = {
            "key": str(instance.key),
            "name": name,
            "description": {
                "checksum": get_hash(instance.description),
                "storage_address": current_site + reverse("substrapp:metric-description", args=[instance.key]),
            },
            "address": {
                "checksum": get_hash(instance.address),
                "storage_address": current_site + reverse("substrapp:metric-metrics", args=[instance.key]),
            },
            "new_permissions": {
                "public": permissions.get("public"),
                "authorized_ids": permissions.get("authorized_ids"),
            },
            "metadata": metadata,
        }
        with get_orchestrator_client(channel_name) as client:
            return client.register_metric(args)

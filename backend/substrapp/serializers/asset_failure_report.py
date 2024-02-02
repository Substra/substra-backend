from rest_framework import serializers

from api.serializers.utils import SafeSerializerMixin
from substrapp.models import AssetFailureReport


class AssetFailureReportSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    asset_key = serializers.UUIDField()
    creation_date = serializers.DateTimeField()

    class Meta:
        model = AssetFailureReport
        fields = [
            "asset_key",
            "asset_type",
            "creation_date",
            "logs_checksum",
            "logs_address",
            "logs_owner",
        ]

    def to_internal_value(self, data):
        logs = data.pop("logs_address", {})
        data["logs_checksum"] = logs.get("checksum")
        data["logs_address"] = logs.get("storage_address")
        return super().to_internal_value(data)

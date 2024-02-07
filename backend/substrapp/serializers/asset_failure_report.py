from rest_framework import serializers

from api.serializers.utils import SafeSerializerMixin
from api.serializers.utils import URLFieldWithOptionalTLD
from substrapp.models import AssetFailureReport


class AssetFailureReportSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    asset_key = serializers.UUIDField()
    creation_date = serializers.DateTimeField()
    logs_address = URLFieldWithOptionalTLD()

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
        failure_report = dict(data)
        logs = failure_report.pop("logs_address", {})
        failure_report["logs_checksum"] = logs.get("checksum")
        failure_report["logs_address"] = logs.get("storage_address")
        owner = failure_report.pop("owner", "")
        failure_report["logs_owner"] = owner
        return super().to_internal_value(failure_report)

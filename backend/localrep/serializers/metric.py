from typing import Dict

from django.urls import reverse
from rest_framework import serializers

from localrep.models import Metric
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from localrep.serializers.utils import make_addressable_serializer
from localrep.serializers.utils import make_download_process_permission_serializer


class MetricSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    address = make_addressable_serializer("metric")(source="*")
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    description = make_addressable_serializer("description")(source="*")
    permissions = make_download_process_permission_serializer()(source="*")

    class Meta:
        model = Metric
        fields = [
            "address",
            "channel",
            "creation_date",
            "description",
            "key",
            "metadata",
            "name",
            "owner",
            "permissions",
        ]

    def to_representation(self, instance):
        res = super().to_representation(instance)
        request = self.context.get("request")
        if request:
            res["description"]["storage_address"] = request.build_absolute_uri(
                reverse("substrapp:metric-description", args=[res["key"]])
            )
            res["address"]["storage_address"] = request.build_absolute_uri(
                reverse("substrapp:metric-metrics", args=[res["key"]])
            )
        return res

    @staticmethod
    def normalize_metrics_data(data: Dict) -> Dict:
        # The orchestrator returns a "algorithm" field.
        # Localrep expects an "address" field.
        data["address"] = data.pop("algorithm")
        return data

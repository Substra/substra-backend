from rest_framework import serializers

from localrep.models import Metric
from localrep.serializers.utils import PermissionsSerializer
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from localrep.serializers.utils import make_addressable_serializer


class MetricSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    address = make_addressable_serializer("metric")(source="*")
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    description = make_addressable_serializer("description")(source="*")
    permissions = PermissionsSerializer(source="*")

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

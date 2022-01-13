from rest_framework import serializers

from localrep.models import Metric
from localrep.serializers.utils import PermissionsSerializer
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from localrep.serializers.utils import make_addressable_serializer


class MetricSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    description = make_addressable_serializer("description")(source="*")
    address = make_addressable_serializer("metric")(source="*")
    permissions = PermissionsSerializer(source="*")
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)

    class Meta:
        model = Metric
        fields = [
            "key",
            "name",
            "owner",
            "creation_date",
            "metadata",
            "description",
            "address",
            "permissions",
            "channel",
        ]

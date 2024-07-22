from django.urls import reverse
from rest_framework import serializers

from api.models import DataManager
from api.serializers.utils import SafeSerializerMixin
from api.serializers.utils import get_channel_choices
from api.serializers.utils import make_addressable_serializer
from api.serializers.utils import make_download_process_permission_serializer
from api.serializers.utils import make_permission_serializer


class DataManagerSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    description = make_addressable_serializer("description")(source="*")
    logs_permission = make_permission_serializer("logs_permission")(source="*")
    opener = make_addressable_serializer("opener")(source="*")
    permissions = make_download_process_permission_serializer()(source="*")

    class Meta:
        model = DataManager
        fields = [
            "channel",
            "creation_date",
            "description",
            "key",
            "logs_permission",
            "metadata",
            "name",
            "opener",
            "owner",
            "permissions",
        ]

    def to_representation(self, instance):
        res = super().to_representation(instance)
        request = self.context.get("request")
        if request:
            res["description"]["storage_address"] = request.build_absolute_uri(
                reverse("api:data_manager_permissions-description", args=[res["key"]])
            )
            res["opener"]["storage_address"] = request.build_absolute_uri(
                reverse("api:data_manager_permissions-opener", args=[res["key"]])
            )
        return res


class DataManagerWithRelationsSerializer(DataManagerSerializer):
    data_sample_keys = serializers.PrimaryKeyRelatedField(
        source="data_samples",
        many=True,
        read_only=True,
    )

    class Meta:
        model = DataManager
        fields = DataManagerSerializer.Meta.fields + [
            "data_sample_keys",
        ]

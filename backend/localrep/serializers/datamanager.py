from rest_framework import serializers

from localrep.models import DataManager
from localrep.serializers.utils import PermissionsSerializer
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from localrep.serializers.utils import make_addressable_serializer
from localrep.serializers.utils import make_permission_serializer


class DataManagerSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    description = make_addressable_serializer("description")(source="*")
    logs_permission = make_permission_serializer("logs_permission")(source="*")
    opener = make_addressable_serializer("opener")(source="*")
    permissions = PermissionsSerializer(source="*")

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
            "type",
        ]


class DataManagerWithRelationsSerializer(DataManagerSerializer):
    test_data_sample_keys = serializers.PrimaryKeyRelatedField(
        source="get_test_data_samples",
        many=True,
        read_only=True,
    )
    train_data_sample_keys = serializers.PrimaryKeyRelatedField(
        source="get_train_data_samples",
        many=True,
        read_only=True,
    )

    class Meta:
        model = DataManager
        fields = DataManagerSerializer.Meta.fields + [
            "test_data_sample_keys",
            "train_data_sample_keys",
        ]

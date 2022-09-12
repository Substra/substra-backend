from rest_framework import serializers

from api.models import DataManager
from api.models import DataSample
from api.serializers.utils import SafeSerializerMixin
from api.serializers.utils import get_channel_choices


class DataSampleSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    data_manager_keys = serializers.PrimaryKeyRelatedField(
        source="data_managers",
        many=True,
        queryset=DataManager.objects.all(),
    )

    class Meta:
        model = DataSample
        fields = [
            "channel",
            "creation_date",
            "data_manager_keys",
            "key",
            "owner",
            "test_only",
        ]

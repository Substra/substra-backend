from rest_framework import serializers

from localrep.models import DataManager
from localrep.models import DataSample
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices


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

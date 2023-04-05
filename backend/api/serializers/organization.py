from rest_framework import serializers

from api.models import ChannelOrganization
from api.serializers.utils import SafeSerializerMixin
from api.serializers.utils import get_channel_choices
from substrapp.utils import get_owner


class ChannelOrganizationSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    id = serializers.CharField(max_length=64, source="organization_id")
    address = serializers.CharField(max_length=200, required=False, allow_blank=True)
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = ChannelOrganization
        fields = ["id", "address", "creation_date", "channel", "is_current"]

    def get_is_current(self, obj):
        return obj.organization_id == get_owner()

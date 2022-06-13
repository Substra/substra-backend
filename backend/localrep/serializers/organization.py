from rest_framework import serializers

from localrep.models import ChannelOrganization
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from substrapp.utils import get_owner


class ChannelOrganizationSerializer(serializers.ModelSerializer, SafeSerializerMixin):

    id = serializers.CharField(max_length=64, source="organization_id")
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = ChannelOrganization
        fields = ["id", "creation_date", "channel", "is_current"]

    def get_is_current(self, obj):
        return obj.organization_id == get_owner()

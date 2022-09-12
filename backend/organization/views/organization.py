from rest_framework import mixins
from rest_framework.viewsets import ModelViewSet

from api.models import ChannelOrganization as ChannelOrganizationRep
from api.serializers import ChannelOrganizationSerializer as ChannelOrganizationRepSerializer
from api.views.utils import get_channel_name


class OrganizationViewSet(ModelViewSet, mixins.ListModelMixin):
    serializer_class = ChannelOrganizationRepSerializer

    def get_queryset(self):
        return ChannelOrganizationRep.objects.filter(channel=get_channel_name(self.request))

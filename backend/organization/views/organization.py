from rest_framework import mixins
from rest_framework.viewsets import ModelViewSet

from localrep.models import ChannelOrganization as ChannelOrganizationRep
from localrep.serializers import ChannelOrganizationSerializer as ChannelOrganizationRepSerializer
from localrep.views.utils import get_channel_name


class OrganizationViewSet(ModelViewSet, mixins.ListModelMixin):
    serializer_class = ChannelOrganizationRepSerializer

    def get_queryset(self):
        return ChannelOrganizationRep.objects.filter(channel=get_channel_name(self.request))

from rest_framework import mixins
from rest_framework.viewsets import ModelViewSet

from localrep.models import ChannelNode as ChannelNodeRep
from localrep.serializers import ChannelNodeSerializer as ChannelNodeRepSerializer
from substrapp.views.utils import get_channel_name


class NodeViewSet(ModelViewSet, mixins.ListModelMixin):
    serializer_class = ChannelNodeRepSerializer

    def get_queryset(self):
        return ChannelNodeRep.objects.filter(channel=get_channel_name(self.request))

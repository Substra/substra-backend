from rest_framework import status, mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.ledger.api import query_ledger
from substrapp.ledger.exceptions import LedgerError
from substrapp.utils import get_owner
from substrapp.views.utils import get_channel_name


class NodeViewSet(mixins.ListModelMixin,
                  GenericViewSet):
    ledger_query_call = 'queryNodes'

    def get_queryset(self):
        return []

    def list(self, request, *args, **kwargs):
        try:
            nodes = query_ledger(get_channel_name(request), fcn=self.ledger_query_call)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        current_node_id = get_owner()
        for node in nodes:
            node.update({
                'is_current': node['id'] == current_node_id,
            })
        return Response(nodes, status=status.HTTP_200_OK)

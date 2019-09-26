from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.ledger_utils import query_ledger, LedgerError
from substrapp.utils import get_owner


class NodeViewSet(GenericViewSet):
    def list(self, request, *args, **kwargs):
        try:
            nodes = query_ledger(fcn='queryPermissionNodes')
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        current_node_id = get_owner()
        for node in nodes:
            node.update({
                'isCurrent': node['ID'] == current_node_id,
            })
        return Response(nodes, status=status.HTTP_200_OK)

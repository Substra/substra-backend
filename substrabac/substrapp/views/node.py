from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.ledger_utils import query_ledger, LedgerError


class NodeViewSet(GenericViewSet):
    def list(self, request, *args, **kwargs):
        try:
            res = query_ledger(fcn='queryPermissionNodes')
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        nodes = [
            {'node_id': node_id}
            for node_id in res['node_ids']
        ]

        return Response(nodes, status=status.HTTP_200_OK)

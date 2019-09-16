from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.ledger_utils import query_ledger, LedgerError


class PermissionNodeViewSet(GenericViewSet):
    def list(self, request, *args, **kwargs):
        try:
            permission_nodes = query_ledger(fcn='queryPermissionNodes')
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        return Response(permission_nodes, status=status.HTTP_200_OK)

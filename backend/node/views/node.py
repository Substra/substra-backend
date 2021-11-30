import structlog
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from orchestrator.error import OrcError
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import get_owner
from substrapp.views.utils import get_channel_name

logger = structlog.get_logger(__name__)


class NodeViewSet(mixins.ListModelMixin, GenericViewSet):
    def get_queryset(self):
        return []

    def list(self, request, *args, **kwargs):
        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                nodes = client.query_nodes()
        except OrcError as rpc_error:
            return Response({"message": rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.error("cannot list nodes", error=e)
            return Response({"message": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        current_node_id = get_owner()
        for node in nodes:
            node.update(
                {
                    "is_current": node["id"] == current_node_id,
                }
            )

        return Response(nodes, status=status.HTTP_200_OK)

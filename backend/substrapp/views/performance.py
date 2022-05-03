import structlog
from rest_framework import mixins
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

from libs.pagination import LargePageNumberPagination
from localrep.models import Performance as PerformanceRep
from localrep.serializers import CPPerformanceSerializer as CPPerformanceRepSerializer
from substrapp.views.utils import get_channel_name

logger = structlog.get_logger(__name__)


class CPPerformanceViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = CPPerformanceRepSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["compute_task__rank", "compute_task__worker", "compute_task__round_idx"]
    ordering = ["compute_task__rank", "compute_task__worker"]
    pagination_class = LargePageNumberPagination

    def get_queryset(self):
        return (
            PerformanceRep.objects.filter(channel=get_channel_name(self.request))
            .select_related("compute_task", "metric")
            .filter(compute_task__compute_plan_id=self.kwargs.get("compute_plan_pk"))
            .distinct()
        )

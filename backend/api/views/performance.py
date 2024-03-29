import csv

import structlog
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F
from django.db.models import Q
from django.db.models import Value
from django.http import StreamingHttpResponse
from django_filters.rest_framework import DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

import orchestrator.computeplan_pb2 as computeplan_pb2
from api.models import ComputePlan as ComputePlan
from api.models import Performance as Performance
from api.serializers import CPPerformanceSerializer as CPPerformanceSerializer
from api.serializers import ExportPerformanceSerializer as ExportPerformanceSerializer
from api.views.computeplan import ComputePlanMetadataFilter
from api.views.filters_utils import CharInFilter
from api.views.filters_utils import ChoiceInFilter
from api.views.filters_utils import MatchFilter
from api.views.filters_utils import UUIDInFilter
from api.views.utils import get_channel_name
from libs.pagination import LargePageNumberPagination

logger = structlog.get_logger(__name__)


class CPPerformanceViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = CPPerformanceSerializer
    pagination_class = None
    filter_backends = [OrderingFilter]
    ordering_fields = [
        "compute_task_output__task__rank",
        "compute_task_output__task__worker",
        "compute_task_output__task__metadata__round_idx",
    ]
    ordering = ["compute_task_output__task__rank", "compute_task_output__task__worker"]
    pagination_class = LargePageNumberPagination

    def _get_cp_ranks_and_rounds(self, compute_plan_pk):
        return (
            ComputePlan.objects.filter(channel=get_channel_name(self.request), key=compute_plan_pk)
            .annotate(
                # List all existing tasks ranks for a given compute plan
                compute_tasks_distinct_ranks=ArrayAgg(
                    "compute_tasks__rank",
                    distinct=True,
                    filter=Q(compute_tasks__rank__isnull=False),
                    default=Value([]),
                ),
                # List all existing tasks round indexes for a given compute plan
                compute_tasks_distinct_rounds=ArrayAgg(
                    "compute_tasks__metadata__round_idx",
                    distinct=True,
                    filter=Q(compute_tasks__metadata__round_idx__isnull=False),
                    default=Value([]),
                ),
            )
            .values("compute_tasks_distinct_ranks", "compute_tasks_distinct_rounds")
        )

    def get_queryset(self):
        return (
            Performance.objects.filter(
                channel=get_channel_name(self.request),
                compute_task_output__task__compute_plan_id=self.kwargs.get("compute_plan_pk"),
            )
            .select_related(
                "compute_task_output",
            )
            .prefetch_related("compute_task_output__task")
            .distinct()
        )

    def list(self, request, compute_plan_pk):
        queryset = self.filter_queryset(self.get_queryset())
        cp_stats = self._get_cp_ranks_and_rounds(compute_plan_pk).first()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data, "compute_plan_statistics": cp_stats})


class PerformanceFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter(field_name="compute_task_output__task__compute_plan__creation_date")
    start_date = DateTimeFromToRangeFilter(field_name="compute_task_output__task__compute_plan__start_date")
    end_date = DateTimeFromToRangeFilter(field_name="compute_task_output__task__compute_plan__end_date")
    status = ChoiceInFilter(
        field_name="compute_task_output__task__compute_plan__status",
        choices=ComputePlan.Status.choices,
    )
    key = UUIDInFilter(field_name="compute_task_output__task__compute_plan__key")
    owner = CharInFilter(field_name="compute_task_output__task__compute_plan__owner")
    identifier = CharInFilter(field_name="compute_task_output__identifier")


class PerformanceMatchFilter(MatchFilter):
    default_search_fields = ("compute_plan_key", "compute_plan_name")


def _build_csv_headers(request) -> list:
    headers = [
        "compute_plan_key",
        "compute_plan_name",
        "compute_plan_tag",
        "compute_plan_status",
        "compute_plan_start_date",
        "compute_plan_end_date",
    ]
    if request.query_params.get("metadata_columns"):
        for md in request.query_params.get("metadata_columns").split(","):
            headers.append(md)
    headers.extend(["identifier", "worker", "task_rank", "task_round", "performance"])
    return headers


def _build_row(obj, headers) -> list:
    row = []
    for field in headers:
        row.append(obj.get(field, ""))
    return row


def map_compute_plan_status(value) -> str:
    return computeplan_pb2.ComputePlanStatus.Name(value)


class PerformanceViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = ExportPerformanceSerializer
    filter_backends = [PerformanceMatchFilter, OrderingFilter, DjangoFilterBackend, ComputePlanMetadataFilter]
    ordering_fields = ["task_rank", "task_round", "worker"]
    ordering = ["task_rank", "task_round", "worker"]
    pagination_class = LargePageNumberPagination
    filterset_class = PerformanceFilter

    def get_queryset(self):
        metadata = {}
        if self.request.query_params.get("metadata_columns"):
            for md in self.request.query_params.get("metadata_columns").split(","):
                metadata[md] = F("compute_task_output__task__compute_plan__metadata__" + md)

        return (
            Performance.objects.filter(channel=get_channel_name(self.request))
            .select_related("compute_task_output__task", "compute_task_output__task__compute_plan")
            .annotate(
                compute_plan_key=F("compute_task_output__task__compute_plan__key"),
                compute_plan_name=F("compute_task_output__task__compute_plan__name"),
                compute_plan_tag=F("compute_task_output__task__compute_plan__tag"),
                compute_plan_status=F("compute_task_output__task__compute_plan__status"),
                compute_plan_start_date=F("compute_task_output__task__compute_plan__start_date"),
                compute_plan_end_date=F("compute_task_output__task__compute_plan__end_date"),
                compute_plan_metadata=F("compute_task_output__task__compute_plan__metadata"),
                worker=F("compute_task_output__task__worker"),
                task_rank=F("compute_task_output__task__rank"),
                task_round=F("compute_task_output__task__metadata__round_idx"),
                identifier=F("compute_task_output__identifier"),
                performance=F("value"),
                **metadata,
            )
            .values()
        )

    def write(self, value):
        """Write the value by returning it."""
        return value

    def generate_rows(self):
        headers = _build_csv_headers(self.request)
        queryset = self.filter_queryset(self.get_queryset())
        yield headers
        if queryset.exists():
            for perf in queryset.iterator():
                yield _build_row(perf, headers)

    @action(detail=False, methods=["get"])
    def export(self, request):
        writer = csv.writer(self)

        return StreamingHttpResponse(
            (writer.writerow(row) for row in self.generate_rows()),
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="compute_plans.csv"'},
        )

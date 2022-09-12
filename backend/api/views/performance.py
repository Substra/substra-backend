import csv

import structlog
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F
from django.db.models import Q
from django.http import StreamingHttpResponse
from django_filters.rest_framework import DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

import orchestrator.computeplan_pb2 as computeplan_pb2
from api.models import ComputePlan as ComputePlanRep
from api.models import Performance as PerformanceRep
from api.serializers import CPPerformanceSerializer as CPPerformanceRepSerializer
from api.serializers import ExportPerformanceSerializer as ExportPerformanceRepSerializer
from api.views.filters_utils import CharInFilter
from api.views.filters_utils import ChoiceInFilter
from api.views.filters_utils import MatchFilter
from api.views.filters_utils import UUIDInFilter
from api.views.utils import get_channel_name
from libs.pagination import LargePageNumberPagination

logger = structlog.get_logger(__name__)


class CPPerformanceViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = CPPerformanceRepSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["compute_task__rank", "compute_task__worker", "compute_task__metadata__round_idx"]
    ordering = ["compute_task__rank", "compute_task__worker"]
    pagination_class = LargePageNumberPagination

    def _get_cp_ranks_and_rounds(self, compute_plan_pk):
        return (
            ComputePlanRep.objects.filter(channel=get_channel_name(self.request), key=compute_plan_pk)
            .annotate(
                # List all existing tasks ranks for a given compute plan
                compute_tasks_distinct_ranks=ArrayAgg(
                    "compute_tasks__rank", distinct=True, filter=Q(compute_tasks__rank__isnull=False)
                ),
                # List all existing tasks round indexes for a given compute plan
                compute_tasks_distinct_rounds=ArrayAgg(
                    "compute_tasks__metadata__round_idx",
                    distinct=True,
                    filter=Q(compute_tasks__metadata__round_idx__isnull=False),
                ),
            )
            .values("compute_tasks_distinct_ranks", "compute_tasks_distinct_rounds")
        )

    def get_queryset(self):
        return (
            PerformanceRep.objects.filter(channel=get_channel_name(self.request))
            .filter(compute_task__compute_plan_id=self.kwargs.get("compute_plan_pk"))
            .select_related("compute_task", "metric")
            .distinct()
        )

    def list(self, request, compute_plan_pk):
        queryset = self.filter_queryset(self.get_queryset())
        cp_stats = self._get_cp_ranks_and_rounds(compute_plan_pk).first()

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        response.data["compute_plan_statistics"] = cp_stats
        return response


class PerformanceRepFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter(field_name="compute_task__compute_plan__creation_date")
    start_date = DateTimeFromToRangeFilter(field_name="compute_task__compute_plan__start_date")
    end_date = DateTimeFromToRangeFilter(field_name="compute_task__compute_plan__end_date")
    status = ChoiceInFilter(
        field_name="compute_task__compute_plan__status",
        choices=ComputePlanRep.Status.choices,
    )
    key = UUIDInFilter(field_name="compute_task__compute_plan__key")
    owner = CharInFilter(field_name="compute_task__compute_plan__owner")


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
    if request.query_params.get("metadata"):
        for md in request.query_params.get("metadata").split(","):
            headers.append(md)
    headers.extend(["metric_name", "worker", "test_task_rank", "test_task_round", "performance"])
    return headers


def _build_row(obj, headers) -> list:
    row = []
    for field in headers:
        row.append(obj.get(field, ""))
    return row


def map_compute_plan_status(value) -> str:
    return computeplan_pb2.ComputePlanStatus.Name(value)


class PerformanceViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = ExportPerformanceRepSerializer
    filter_backends = [PerformanceMatchFilter, OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["test_task_rank", "test_task_round", "worker"]
    ordering = ["test_task_rank", "test_task_round", "worker"]
    pagination_class = LargePageNumberPagination
    filterset_class = PerformanceRepFilter

    def get_queryset(self):
        metadata = {}
        if self.request.query_params.get("metadata"):
            for md in self.request.query_params.get("metadata").split(","):
                metadata[md] = F("compute_task__compute_plan__metadata__" + md)

        return (
            PerformanceRep.objects.filter(channel=get_channel_name(self.request))
            .select_related("compute_task", "metric", "compute_task__compute_plan")
            .annotate(
                compute_plan_key=F("compute_task__compute_plan__key"),
                compute_plan_name=F("compute_task__compute_plan__name"),
                compute_plan_tag=F("compute_task__compute_plan__tag"),
                compute_plan_status=F("compute_task__compute_plan__status"),
                compute_plan_start_date=F("compute_task__compute_plan__start_date"),
                compute_plan_end_date=F("compute_task__compute_plan__end_date"),
                compute_plan_metadata=F("compute_task__compute_plan__metadata"),
                worker=F("compute_task__worker"),
                test_task_rank=F("compute_task__rank"),
                test_task_round=F("compute_task__metadata__round_idx"),
                metric_name=F("metric__name"),
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

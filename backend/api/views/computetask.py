import structlog
from django.db import models
from django.db.models.expressions import RawSQL
from django.db.models.functions import Coalesce
from django.db.models.functions import Extract
from django.db.models.functions import JSONObject
from django.db.models.functions import Now
from django_filters.rest_framework import BaseInFilter
from django_filters.rest_framework import CharFilter
from django_filters.rest_framework import DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from django_filters.rest_framework import RangeFilter
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

from api.errors import AlreadyExistsError
from api.errors import BadRequestError
from api.models import ComputePlan
from api.models import ComputeTask
from api.models import ComputeTaskInputAsset
from api.models import ComputeTaskOutputAsset
from api.models.function import FunctionInput
from api.models.function import FunctionOutput
from api.serializers import ComputeTaskInputAssetSerializer
from api.serializers import ComputeTaskOutputAssetSerializer
from api.serializers import ComputeTaskSerializer
from api.views.filters_utils import CharInFilter
from api.views.filters_utils import ChoiceInFilter
from api.views.filters_utils import MatchFilter
from api.views.filters_utils import MetadataFilterBackend
from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from api.views.utils import validate_key
from api.views.utils import validate_metadata
from libs.pagination import DefaultPageNumberPagination
from orchestrator import computetask
from orchestrator.resources import TAG_KEY
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger(__name__)


def _register_in_orchestrator(tasks_data, channel_name):
    """Register computetask in orchestrator."""
    batch = {}
    for task_data in tasks_data:
        orc_task = {
            "key": task_data["key"],
            "function_key": task_data.get("function_key"),
            "compute_plan_key": task_data["compute_plan_key"],
            "inputs": task_data.get("inputs", []),
            "outputs": task_data.get("outputs", {}),
            "metadata": task_data.get("metadata") or {},
        }

        validate_metadata(orc_task["metadata"])
        orc_task["metadata"][TAG_KEY] = task_data.get("tag") or ""

        if "worker" in task_data:
            orc_task["worker"] = task_data["worker"]

        batch[orc_task["key"]] = orc_task

    with get_orchestrator_client(channel_name) as client:
        return client.register_tasks({"tasks": list(batch.values())})


def task_bulk_create(request):
    """Create a batch of tasks (with various categories) with same CP keys

    The workflow is composed of several steps:
    - Register assets in the orchestrator.
    - Save metadata in local database.
    """

    # Step1: register asset in orchestrator
    compute_plan_keys = [task["compute_plan_key"] for task in request.data["tasks"]]
    compute_plans = ComputePlan.objects.filter(key__in=compute_plan_keys)
    if len(compute_plans) == 0:
        raise BadRequestError("Invalid compute plan key")
    if len(compute_plans) > 1:
        raise BadRequestError("All tasks should have the same compute plan key")
    compute_plan = compute_plans[0]
    orc_data = _register_in_orchestrator(request.data["tasks"], get_channel_name(request))

    # Step2: save metadata in local database
    data = []
    for task in orc_data:
        api_data = computetask.orc_to_api(task)
        api_data["channel"] = get_channel_name(request)
        api_serializer = ComputeTaskSerializer(data=api_data)
        try:
            api_serializer.save_if_not_exists()
        except AlreadyExistsError:
            # May happen if the events app already processed the event pushed by the orchestrator
            compute_task = ComputeTask.objects.get(key=api_data["key"])
            api_task_data = ComputeTaskSerializer(compute_task).data
        else:
            api_task_data = api_serializer.data
        data.append(api_task_data)

    compute_plan.update_dates()
    compute_plan.update_status()
    return ApiResponse(data, status=status.HTTP_200_OK)


def validate_status_and_map_cp_key(key, values):
    if key == "status":
        try:
            for value in values:
                getattr(ComputeTask.Status, value)
        except AttributeError as e:
            raise BadRequestError(f"Wrong {key} value: {e}")
    elif key == "compute_plan_key":
        key = "compute_plan_id"
    return key, values


class ComputePlanKeyOrderingFilter(OrderingFilter):
    """Allow ordering on compute_plan_key."""

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        return [v.replace("compute_plan_key", "compute_plan_id") for v in ordering]


class ComputeTaskMetadataFilter(MetadataFilterBackend):
    def _apply_filters(self, queryset, filter_keys):
        return queryset.annotate(
            metadata_filters=JSONObject(
                **{
                    f"{filter_key}": RawSQL(
                        "api_computetask.metadata ->> %s",
                        (filter_key,),
                    )
                    for filter_key in filter_keys
                }
            )
        )


class ComputeTaskFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter()
    start_date = DateTimeFromToRangeFilter()
    end_date = DateTimeFromToRangeFilter()
    status = ChoiceInFilter(
        field_name="status",
        choices=ComputeTask.Status.choices,
    )
    compute_plan_key = CharInFilter(field_name="compute_plan__key")
    function_key = CharFilter(field_name="function__key", distinct=True, label="function_key")
    duration = RangeFilter(label="duration")

    class Meta:
        model = ComputeTask
        fields = {
            "key": ["exact"],
            "owner": ["exact"],
            "rank": ["exact"],
            "worker": ["exact"],
            "tag": ["exact"],
        }
        filter_overrides = {
            models.CharField: {
                "filter_class": BaseInFilter,
                "extra": lambda f: {
                    "lookup_expr": "in",
                },
            },
            models.IntegerField: {
                "filter_class": BaseInFilter,
                "extra": lambda f: {
                    "lookup_expr": "in",
                },
            },
            models.UUIDField: {
                "filter_class": BaseInFilter,
                "extra": lambda f: {
                    "lookup_expr": "in",
                },
            },
        }


class InputAssetFilter(FilterSet):
    kind = ChoiceInFilter(field_name="asset_kind", choices=FunctionInput.Kind.choices)

    class Meta:
        model = ComputeTaskInputAsset
        fields = ["kind"]


class OutputAssetFilter(FilterSet):
    kind = ChoiceInFilter(field_name="asset_kind", choices=FunctionOutput.Kind.choices)

    class Meta:
        model = ComputeTaskOutputAsset
        fields = ["kind"]


class ComputeTaskViewSetConfig:
    filter_backends = (ComputePlanKeyOrderingFilter, MatchFilter, DjangoFilterBackend, ComputeTaskMetadataFilter)
    ordering_fields = [
        "creation_date",
        "start_date",
        "end_date",
        "key",
        "owner",
        "rank",
        "status",
        "function__name",
        "tag",
        "compute_plan_key",
        "duration",
    ]
    ordering = ["creation_date", "key"]
    pagination_class = DefaultPageNumberPagination
    search_fields = ("key",)
    filterset_class = ComputeTaskFilter


class ComputeTaskViewSet(ComputeTaskViewSetConfig, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    serializer_class = ComputeTaskSerializer

    @action(methods=["post"], detail=False, url_name="bulk_create")
    def bulk_create(self, request, *args, **kwargs):
        return task_bulk_create(request)

    @action(detail=True, url_name="input_assets")
    def input_assets(self, request, pk):
        input_assets = ComputeTaskInputAsset.objects.filter(task_input__task_id=pk).order_by(
            "task_input__identifier", "task_input__position"
        )
        input_assets = InputAssetFilter(request.GET, queryset=input_assets).qs

        context = {"request": request}
        page = self.paginate_queryset(input_assets)
        if page is not None:
            serializer = ComputeTaskInputAssetSerializer(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = ComputeTaskInputAssetSerializer(input_assets, many=True, context=context)
        return ApiResponse(serializer.data)

    @action(detail=True, url_name="output_assets")
    def output_assets(self, request, pk):
        output_assets = ComputeTaskOutputAsset.objects.filter(task_output__task_id=pk).order_by(
            "task_output__identifier"
        )
        output_assets = OutputAssetFilter(request.GET, queryset=output_assets).qs

        context = {"request": request}
        page = self.paginate_queryset(output_assets)
        if page is not None:
            serializer = ComputeTaskOutputAssetSerializer(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = ComputeTaskOutputAssetSerializer(output_assets, many=True, context=context)
        return ApiResponse(serializer.data)

    def get_queryset(self):
        return (
            ComputeTask.objects.filter(channel=get_channel_name(self.request))
            .select_related("function")
            .prefetch_related("inputs", "outputs", "function__inputs", "function__outputs")
            .annotate(
                # Using 0 as default value instead of None for ordering purpose, as default
                # Postgres behavior considers null as greater than any other value.
                duration=models.Case(
                    models.When(start_date__isnull=True, then=0),
                    default=Extract(Coalesce("end_date", Now()) - models.F("start_date"), "epoch"),
                )
            )
        )


class CPTaskViewSet(ComputeTaskViewSetConfig, mixins.ListModelMixin, GenericViewSet):
    serializer_class = ComputeTaskSerializer

    def get_queryset(self):
        compute_plan_key = self.kwargs.get("compute_plan_pk")
        validate_key(compute_plan_key)

        return (
            ComputeTask.objects.filter(channel=get_channel_name(self.request))
            .filter(compute_plan__key=compute_plan_key)
            .select_related("function")
            .prefetch_related("function__inputs", "function__outputs")
            .annotate(
                # Using 0 as default value instead of None for ordering purpose, as default
                # Postgres behavior considers null as greater than any other value.
                duration=models.Case(
                    models.When(start_date__isnull=True, then=0),
                    default=Extract(Coalesce("end_date", Now()) - models.F("start_date"), "epoch"),
                )
            )
        )

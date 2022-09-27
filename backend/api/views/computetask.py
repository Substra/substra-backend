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
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

from api.errors import AlreadyExistsError
from api.errors import BadRequestError
from api.models import ComputePlan
from api.models import ComputeTask
from api.serializers import ComputeTaskSerializer
from api.serializers import ComputeTaskWithRelationshipsSerializer
from api.views.filters_utils import CharInFilter
from api.views.filters_utils import ChoiceInFilter
from api.views.filters_utils import MatchFilter
from api.views.filters_utils import MetadataFilterBackend
from api.views.utils import CP_BASENAME_PREFIX
from api.views.utils import TASK_CATEGORY
from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from api.views.utils import validate_key
from api.views.utils import validate_metadata
from libs.pagination import DefaultPageNumberPagination
from orchestrator import computetask
from orchestrator.resources import TAG_KEY
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger(__name__)


EXTRA_DATA_FIELD = {
    ComputeTask.Category.TASK_TRAIN: "train",
    ComputeTask.Category.TASK_PREDICT: "predict",
    ComputeTask.Category.TASK_TEST: "test",
    ComputeTask.Category.TASK_AGGREGATE: "aggregate",
    ComputeTask.Category.TASK_COMPOSITE: "composite",
}


def _compute_extra_data(orc_task, task_data):
    if orc_task["category"] == ComputeTask.Category.TASK_TRAIN:
        return {
            "data_manager_key": task_data["data_manager_key"],
            "data_sample_keys": task_data["train_data_sample_keys"],
        }

    elif orc_task["category"] in [ComputeTask.Category.TASK_PREDICT, ComputeTask.Category.TASK_TEST]:
        return {
            "data_manager_key": task_data["data_manager_key"],
            "data_sample_keys": task_data["test_data_sample_keys"],
        }

    elif orc_task["category"] == ComputeTask.Category.TASK_AGGREGATE:
        return {}

    elif orc_task["category"] == ComputeTask.Category.TASK_COMPOSITE:
        return {
            "data_manager_key": task_data["data_manager_key"],
            "data_sample_keys": task_data["train_data_sample_keys"],
        }

    else:
        raise Exception(f'Task type "{orc_task["category"]}" not handled')


def _register_in_orchestrator(tasks_data, channel_name):
    """Register computetask in orchestrator."""
    batch = {}
    for task_data in tasks_data:
        orc_task = {
            "key": task_data["key"],
            "category": task_data["category"],
            "algo_key": task_data.get("algo_key"),
            "compute_plan_key": task_data["compute_plan_key"],
            "inputs": task_data.get("inputs", []),
            "outputs": task_data.get("outputs", {}),
            "metadata": task_data.get("metadata") or {},
        }

        validate_metadata(orc_task["metadata"])
        orc_task["metadata"][TAG_KEY] = task_data.get("tag") or ""

        extra_data_field = EXTRA_DATA_FIELD[orc_task["category"]]
        orc_task[extra_data_field] = _compute_extra_data(orc_task, task_data)

        if "worker" in task_data:
            orc_task["worker"] = task_data["worker"]

        batch[orc_task["key"]] = orc_task

    with get_orchestrator_client(channel_name) as client:
        return client.register_tasks({"tasks": list(batch.values())})


@api_view(["POST"])
def task_bulk_create_view(request):
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
    category = ChoiceInFilter(
        field_name="category",
        choices=ComputeTask.Category.choices,
    )
    compute_plan_key = CharInFilter(field_name="compute_plan__key")
    algo_key = CharFilter(field_name="algo__key", distinct=True, label="algo_key")
    dataset_key = CharFilter(field_name="data_manager__key", distinct=True, label="dataset_key")
    data_sample_key = CharInFilter(field_name="data_samples__key", distinct=True, label="data_sample_key")
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


class ComputeTaskViewSetConfig:
    serializer_class = ComputeTaskSerializer
    filter_backends = (ComputePlanKeyOrderingFilter, MatchFilter, DjangoFilterBackend, ComputeTaskMetadataFilter)
    ordering_fields = [
        "creation_date",
        "start_date",
        "end_date",
        "key",
        "owner",
        "category",
        "rank",
        "status",
        "worker",
        "tag",
        "compute_plan_key",
        "duration",
    ]
    ordering = ["creation_date", "key"]
    pagination_class = DefaultPageNumberPagination
    search_fields = ("key",)
    filterset_class = ComputeTaskFilter

    @property
    def short_basename(self):
        return self.basename.removeprefix(CP_BASENAME_PREFIX)

    @property
    def category(self):
        return TASK_CATEGORY[self.short_basename]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ComputeTaskWithRelationshipsSerializer
        return ComputeTaskSerializer

    def get_queryset(self):
        queryset = (
            ComputeTask.objects.filter(channel=get_channel_name(self.request), category=self.category)
            .select_related("algo")
            .annotate(
                # Using 0 as default value instead of None for ordering purpose, as default
                # Postgres behavior considers null as greater than any other value.
                duration=models.Case(
                    models.When(start_date__isnull=True, then=0),
                    default=Extract(Coalesce("end_date", Now()) - models.F("start_date"), "epoch"),
                )
            )
        )
        if self.category == ComputeTask.Category.TASK_TEST:
            queryset = queryset.prefetch_related("performances")
        else:
            queryset = queryset.prefetch_related("models")
        return queryset


class ComputeTaskViewSet(ComputeTaskViewSetConfig, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    pass


class CPTaskViewSet(ComputeTaskViewSetConfig, mixins.ListModelMixin, GenericViewSet):
    def get_queryset(self):
        compute_plan_key = self.kwargs.get("compute_plan_pk")
        validate_key(compute_plan_key)

        queryset = super().get_queryset()
        return queryset.filter(compute_plan__key=compute_plan_key).annotate(
            # Using 0 as default value instead of None for ordering purpose, as default
            # Postgres behavior considers null as greater than any other value.
            duration=models.Case(
                models.When(start_date__isnull=True, then=0),
                default=Extract(Coalesce("end_date", Now()) - models.F("start_date"), "epoch"),
            )
        )

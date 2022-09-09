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

from libs.pagination import DefaultPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import ComputePlan as ComputePlanRep
from localrep.models import ComputeTask as ComputeTaskRep
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from localrep.serializers import ComputeTaskWithRelationshipsSerializer as ComputeTaskWithRelationshipsRepSerializer
from localrep.views.filters_utils import CharInFilter
from localrep.views.filters_utils import ChoiceInFilter
from localrep.views.filters_utils import MatchFilter
from localrep.views.filters_utils import MetadataFilterBackend
from localrep.views.utils import CP_BASENAME_PREFIX
from localrep.views.utils import TASK_CATEGORY
from localrep.views.utils import ApiResponse
from localrep.views.utils import ValidationExceptionError
from localrep.views.utils import get_channel_name
from localrep.views.utils import validate_key
from orchestrator import computetask
from substrapp import exceptions
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger(__name__)


EXTRA_DATA_FIELD = {
    ComputeTaskRep.Category.TASK_TRAIN: "train",
    ComputeTaskRep.Category.TASK_PREDICT: "predict",
    ComputeTaskRep.Category.TASK_TEST: "test",
    ComputeTaskRep.Category.TASK_AGGREGATE: "aggregate",
    ComputeTaskRep.Category.TASK_COMPOSITE: "composite",
}


def _compute_extra_data(orc_task, task_data):
    if orc_task["category"] == ComputeTaskRep.Category.TASK_TRAIN:
        return {
            "data_manager_key": task_data["data_manager_key"],
            "data_sample_keys": task_data["train_data_sample_keys"],
        }

    elif orc_task["category"] in [ComputeTaskRep.Category.TASK_PREDICT, ComputeTaskRep.Category.TASK_TEST]:
        return {
            "data_manager_key": task_data["data_manager_key"],
            "data_sample_keys": task_data["test_data_sample_keys"],
        }

    elif orc_task["category"] == ComputeTaskRep.Category.TASK_AGGREGATE:
        return {
            "worker": task_data["worker"],
        }

    elif orc_task["category"] == ComputeTaskRep.Category.TASK_COMPOSITE:
        return {
            "data_manager_key": task_data["data_manager_key"],
            "data_sample_keys": task_data["train_data_sample_keys"],
        }

    else:
        raise Exception(f'Task type "{orc_task["category"]}" not handled')


def _compute_parent_task_keys(orc_task, task_data, batch):
    # Deduplicate parent tasks, but avoid using a set to preserve parents order
    parent_task_keys = list(dict.fromkeys([str(key) for key in (task_data.get("in_models_keys", []) or [])]))

    if orc_task["category"] == ComputeTaskRep.Category.TASK_COMPOSITE:
        # here we need to build a list from the head and trunk models sent by the user
        parent_task_keys = [
            task_data.get(field) for field in ("in_head_model_key", "in_trunk_model_key") if task_data.get(field)
        ]

    elif orc_task["category"] == ComputeTaskRep.Category.TASK_PREDICT:
        if traintuple_id := task_data.get("traintuple_key"):
            parent_task_keys.append(traintuple_id)
        else:
            raise ValidationExceptionError(
                data=[{"traintuple_key": ["This field may not be null."]}],
                key=orc_task["key"],
                st=status.HTTP_400_BAD_REQUEST,
            )

        # try to retrieve parent task in current batch
        parent_task_data = batch.get(parent_task_keys[0])
        # else query the db
        if parent_task_data is None:
            parent_task = ComputeTaskRep.objects.get(key=parent_task_keys[0])
            parent_task_data = {
                "compute_plan_key": str(parent_task.compute_plan_id),
            }
        orc_task["compute_plan_key"] = parent_task_data["compute_plan_key"]

    elif orc_task["category"] == ComputeTaskRep.Category.TASK_TEST:
        if predicttuple_id := task_data.get("predicttuple_key"):
            parent_task_keys.append(predicttuple_id)
        else:
            raise ValidationExceptionError(
                data=[{"predicttuple_key": ["This field may not be null."]}],
                key=orc_task["key"],
                st=status.HTTP_400_BAD_REQUEST,
            )

        # try to retrieve parent task in current batch
        parent_task_data = batch.get(parent_task_keys[0])
        # else query the db
        if parent_task_data is None:
            parent_task = ComputeTaskRep.objects.get(key=parent_task_keys[0])
            parent_task_data = {
                "compute_plan_key": str(parent_task.compute_plan_id),
            }
        orc_task["compute_plan_key"] = parent_task_data["compute_plan_key"]

    orc_task["parent_task_keys"] = parent_task_keys
    return orc_task


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

        if "__tag__" in orc_task["metadata"]:
            raise Exception('"__tag__" cannot be used as a metadata key')
        else:
            orc_task["metadata"]["__tag__"] = task_data.get("tag") or ""

        _compute_parent_task_keys(orc_task, task_data, batch)

        extra_data_field = EXTRA_DATA_FIELD[orc_task["category"]]
        orc_task[extra_data_field] = _compute_extra_data(orc_task, task_data)

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
    compute_plans = ComputePlanRep.objects.filter(key__in=compute_plan_keys)
    if len(compute_plans) == 0:
        raise exceptions.BadRequestError("Invalid compute plan key")
    if len(compute_plans) > 1:
        raise exceptions.BadRequestError("All tasks should have the same compute plan key")
    compute_plan = compute_plans[0]
    orc_data = _register_in_orchestrator(request.data["tasks"], get_channel_name(request))

    # Step2: save metadata in local database
    data = []
    for task in orc_data:
        localrep_data = computetask.orc_to_localrep(task)
        localrep_data["channel"] = get_channel_name(request)
        localrep_serializer = ComputeTaskRepSerializer(data=localrep_data)
        try:
            localrep_serializer.save_if_not_exists()
        except AlreadyExistsError:
            # May happen if the events app already processed the event pushed by the orchestrator
            compute_task = ComputeTaskRep.objects.get(key=localrep_data["key"])
            localrep_task_data = ComputeTaskRepSerializer(compute_task).data
        else:
            localrep_task_data = localrep_serializer.data
        data.append(localrep_task_data)

    compute_plan.update_dates()
    compute_plan.update_status()
    return ApiResponse(data, status=status.HTTP_200_OK)


def validate_status_and_map_cp_key(key, values):
    if key == "status":
        try:
            for value in values:
                getattr(ComputeTaskRep.Status, value)
        except AttributeError as e:
            raise exceptions.BadRequestError(f"Wrong {key} value: {e}")
    elif key == "compute_plan_key":
        key = "compute_plan_id"
    return key, values


class ComputePlanKeyOrderingFilter(OrderingFilter):
    """Allow ordering on compute_plan_key."""

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        return [v.replace("compute_plan_key", "compute_plan_id") for v in ordering]


class ComputeTaskRepMetadataFilter(MetadataFilterBackend):
    def _apply_filters(self, queryset, filter_keys):
        return queryset.annotate(
            metadata_filters=JSONObject(
                **{
                    f"{filter_key}": RawSQL(
                        "localrep_computetask.metadata ->> %s",
                        (filter_key,),
                    )
                    for filter_key in filter_keys
                }
            )
        )


class ComputeTaskRepFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter()
    start_date = DateTimeFromToRangeFilter()
    end_date = DateTimeFromToRangeFilter()
    status = ChoiceInFilter(
        field_name="status",
        choices=ComputeTaskRep.Status.choices,
    )
    category = ChoiceInFilter(
        field_name="category",
        choices=ComputeTaskRep.Category.choices,
    )
    compute_plan_key = CharInFilter(field_name="compute_plan__key")
    algo_key = CharFilter(field_name="algo__key", distinct=True, label="algo_key")
    dataset_key = CharFilter(field_name="data_manager__key", distinct=True, label="dataset_key")
    data_sample_key = CharInFilter(field_name="data_samples__key", distinct=True, label="data_sample_key")
    duration = RangeFilter(label="duration")

    class Meta:
        model = ComputeTaskRep
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
    serializer_class = ComputeTaskRepSerializer
    filter_backends = (ComputePlanKeyOrderingFilter, MatchFilter, DjangoFilterBackend, ComputeTaskRepMetadataFilter)
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
    filterset_class = ComputeTaskRepFilter

    @property
    def short_basename(self):
        return self.basename.removeprefix(CP_BASENAME_PREFIX)

    @property
    def category(self):
        return TASK_CATEGORY[self.short_basename]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ComputeTaskWithRelationshipsRepSerializer
        return ComputeTaskRepSerializer

    def get_queryset(self):
        queryset = (
            ComputeTaskRep.objects.filter(channel=get_channel_name(self.request), category=self.category)
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
        if self.category == ComputeTaskRep.Category.TASK_TEST:
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

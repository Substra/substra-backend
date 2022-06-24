import structlog
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models.functions import Extract
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
from substrapp import exceptions
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import get_owner
from substrapp.views.utils import CP_BASENAME_PREFIX
from substrapp.views.utils import TASK_CATEGORY
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import CharInFilter
from substrapp.views.utils import ChoiceInFilter
from substrapp.views.utils import MatchFilter
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import permissions_intersect
from substrapp.views.utils import permissions_union
from substrapp.views.utils import to_string_uuid
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


EXTRA_DATA_FIELD = {
    ComputeTaskRep.Category.TASK_TRAIN: "train",
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

    elif orc_task["category"] == ComputeTaskRep.Category.TASK_TEST:
        return {
            "metric_keys": task_data["metric_keys"],
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


def _get_task_outputs(channel, task_data, trunk_permissions, tasks_cache=None):
    """
    This function replicates the historical permission rules, originally implemented in the orchestrator.
    In a later iteration, this function will be removed and the permissions will be set explicitly by the client.
    """
    if task_data["category"] == ComputeTaskRep.Category.TASK_TRAIN:
        # Adapted from
        # https://github.com/owkin/orchestrator/blob/a9f7d14867746f58958f30dd6304167d87a6f15c/lib/service/computetask.go#L506
        with get_orchestrator_client(channel) as client:
            algo = client.query_algo(task_data["algo_key"])
            data_manager = client.query_datamanager(task_data["train"]["data_manager_key"])

        permissions = permissions_intersect(algo["permissions"]["process"], data_manager["permissions"]["process"])
        return {"model": {"permissions": permissions}}

    elif task_data["category"] == ComputeTaskRep.Category.TASK_TEST:
        # Performances should always be public
        # Orchestrator will refuse anything else
        return {"performance": {"permissions": {"public": True}}}

    elif task_data["category"] == ComputeTaskRep.Category.TASK_AGGREGATE:
        # Adapted from
        # https://github.com/owkin/orchestrator/blob/a9f7d14867746f58958f30dd6304167d87a6f15c/lib/service/computetask.go#L456-L471
        permissions = {
            "public": False,
            "authorized_ids": [get_owner()],
        }
        for task_key in task_data["parent_task_keys"]:
            perm = _get_parent_task_output_permission(channel, task_key, tasks_cache)
            permissions = permissions_union(permissions, perm)

        return {"model": {"permissions": permissions}}

    elif task_data["category"] == ComputeTaskRep.Category.TASK_COMPOSITE:
        # Adapted from
        # https://github.com/owkin/orchestrator/blob/a9f7d14867746f58958f30dd6304167d87a6f15c/lib/service/computetask.go#L409-L416
        with get_orchestrator_client(channel) as client:
            data_manager = client.query_datamanager(task_data["composite"]["data_manager_key"])

        permissions_local = {"public": False, "authorized_ids": [data_manager["owner"]]}
        permissions_shared = trunk_permissions

        if not permissions_shared["public"]:
            authorized_ids = set(permissions_shared["authorized_ids"])
            authorized_ids.add(data_manager["owner"])
            permissions_shared["authorized_ids"] = list(authorized_ids)

        return {
            "local": {"permissions": permissions_local},
            "shared": {"permissions": permissions_shared},
        }

    else:
        raise Exception(f'Task type "{task_data["category"]}" unknown')


def _get_parent_task_output_permission(channel, task_key, tasks_cache):
    task = None
    perm = None
    from_orchestrator = False

    if tasks_cache:
        task = tasks_cache.get(to_string_uuid(task_key))

    if not task:
        from_orchestrator = True
        with get_orchestrator_client(channel) as client:
            task = client.query_task(task_key)

    if task["category"] == ComputeTaskRep.Category.TASK_TRAIN:
        perm = task["outputs"]["model"]["permissions"]
    elif task["category"] == ComputeTaskRep.Category.TASK_AGGREGATE:
        perm = task["outputs"]["model"]["permissions"]
    elif task["category"] == ComputeTaskRep.Category.TASK_COMPOSITE:
        perm = task["outputs"]["shared"]["permissions"]
    else:
        raise Exception(f"Unknown parent task category: {task['category']}")

    if from_orchestrator:
        return perm["process"]
    else:
        # for results coming from the cache, there's no distinction between process and download permissions
        return perm


def _compute_parent_task_keys(orc_task, task_data, batch):
    # Deduplicate parent tasks, but avoid using a set to preserve parents order
    parent_task_keys = list(dict.fromkeys([str(key) for key in (task_data.get("in_models_keys", []) or [])]))

    if orc_task["category"] == ComputeTaskRep.Category.TASK_COMPOSITE:
        # here we need to build a list from the head and trunk models sent by the user
        parent_task_keys = [
            task_data.get(field) for field in ("in_head_model_key", "in_trunk_model_key") if task_data.get(field)
        ]

    if orc_task["category"] == ComputeTaskRep.Category.TASK_TEST:
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
                "algo_key": str(parent_task.algo_id),
                "compute_plan_key": str(parent_task.compute_plan_id),
            }
        orc_task["algo_key"] = parent_task_data["algo_key"]
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
            "metadata": task_data.get("metadata") or {},
        }

        if "__tag__" in orc_task["metadata"]:
            raise Exception('"__tag__" cannot be used as a metadata key')
        else:
            orc_task["metadata"]["__tag__"] = task_data.get("tag") or ""

        _compute_parent_task_keys(orc_task, task_data, batch)

        extra_data_field = EXTRA_DATA_FIELD[orc_task["category"]]
        orc_task[extra_data_field] = _compute_extra_data(orc_task, task_data)
        trunk_permissions = task_data.get("out_trunk_model_permissions", {})
        orc_task["outputs"] = _get_task_outputs(channel_name, orc_task, trunk_permissions, batch)

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
    registered_tasks_data = _register_in_orchestrator(request.data["tasks"], get_channel_name(request))

    # Step2: save metadata in local database
    data = []
    for localrep_data in registered_tasks_data:
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
    filter_backends = (ComputePlanKeyOrderingFilter, MatchFilter, DjangoFilterBackend)
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
            queryset = queryset.prefetch_related("performances", "metrics")
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

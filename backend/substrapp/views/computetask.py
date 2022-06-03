import uuid

import structlog
from django.db import models
from django_filters.rest_framework import BaseInFilter
from django_filters.rest_framework import CharFilter
from django_filters.rest_framework import DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework import mixins
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

from libs.pagination import DefaultPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import ComputeTask as ComputeTaskRep
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from localrep.serializers import ComputeTaskWithRelationshipsSerializer as ComputeTaskWithRelationshipsRepSerializer
from substrapp import exceptions
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import get_owner
from substrapp.views.filters_utils import CustomSearchFilter
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


CP_TASK_KEY = {
    "aggregatetuple": "aggregatetuple_id",
    "composite_traintuple": "composite_traintuple_id",
    "traintuple": "traintuple_id",
}

TASK_EXTRA_DATA_FIELD = {
    "aggregatetuple": "aggregate",
    "composite_traintuple": "composite",
    "testtuple": "test",
    "traintuple": "train",
}


def _add_task_extra_data(data, task_type, tasks_cache=None):
    if task_type == "composite_traintuple":

        return {
            "data_manager_key": str(data.get("data_manager_key", "") or ""),
            "data_sample_keys": [str(d) for d in (data.get("train_data_sample_keys", []) or [])],
        }

    elif task_type == "testtuple":
        return {
            "metric_keys": data.get("metric_keys", []) or [],
            "data_manager_key": str(data.get("data_manager_key", "") or ""),
            "data_sample_keys": [str(d) for d in (data.get("test_data_sample_keys", []) or [])],
        }

    elif task_type == "aggregatetuple":
        return {
            "worker": data.get("worker", ""),
        }

    elif task_type == "traintuple":
        return {
            "data_manager_key": str(data.get("data_manager_key", "") or ""),
            "data_sample_keys": [str(d) for d in (data.get("train_data_sample_keys", []) or [])],
        }

    else:
        raise Exception(f'Task type "{task_type}" not handled')


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


def build_computetask_data(channel: str, data, task_type, tasks_cache=None, from_compute_plan=False):
    # *in_models_ depends if we use this function from computetask view or compute plan view
    field = "id" if from_compute_plan else "key"

    if from_compute_plan and task_type != "testtuple":
        # users never define testtuple key inside a computeplan request
        # so we need to generate one
        key = to_string_uuid(data.get(CP_TASK_KEY[task_type]))
    else:
        key = str(uuid.uuid4())

    trunk_permissions = data.get("out_trunk_model_permissions", {})
    task_data = {
        "key": key,
        "category": TASK_CATEGORY[task_type],
        "algo_key": data.get("algo_key") or "",
        "compute_plan_key": data.get("compute_plan_key") or "",
        "metadata": data.get("metadata") or {},
    }

    # Deduplicate parent tasks, but avoid using a set to preserve parents order
    parent_task_keys = list(dict.fromkeys([str(key) for key in (data.get(f"in_models_{field}s", []) or [])]))

    if task_type == "composite_traintuple":
        # here we need to build a list from the head and trunk models sent by the user
        parent_task_keys = [data.get(f"in_head_model_{field}"), data.get(f"in_trunk_model_{field}")]
        parent_task_keys = [item for item in parent_task_keys if item]

    if task_type == "testtuple":
        if traintuple_id := data.get(f"traintuple_{field}"):
            parent_task_keys.append(traintuple_id)
        else:
            raise ValidationExceptionError(
                data=[{f"traintuple_{field}": ["This field may not be null."]}],
                key=task_data["key"],
                st=status.HTTP_400_BAD_REQUEST,
            )

        if tasks_cache is not None:
            task_data["algo_key"] = str(tasks_cache.get(to_string_uuid(parent_task_keys[0]), {}).get("algo_key", ""))
            task_data["compute_plan_key"] = str(
                tasks_cache.get(to_string_uuid(parent_task_keys[0]), {}).get("compute_plan_key", "")
            )

        if not (task_data["algo_key"] and task_data["compute_plan_key"]):
            # The training task might already be registered and not part of the current cache or batch
            parent_task = ComputeTaskRep.objects.get(key=to_string_uuid(parent_task_keys[0]))
            task_data["algo_key"] = str(parent_task.algo.key)
            task_data["compute_plan_key"] = str(parent_task.compute_plan.key)

    task_data["parent_task_keys"] = parent_task_keys

    if "__tag__" in task_data["metadata"]:
        raise Exception('"__tag__" cannot be used as a metadata key')
    else:
        task_data["metadata"]["__tag__"] = data.get("tag", "") or ""

    task_data[TASK_EXTRA_DATA_FIELD[task_type]] = _add_task_extra_data(data, task_type, tasks_cache)
    task_data["outputs"] = _get_task_outputs(channel, task_data, trunk_permissions, tasks_cache)

    return task_data


def _register_in_orchestrator(request, basename):
    """Register computetask in orchestrator."""
    orc_task = build_computetask_data(get_channel_name(request), dict(request.data), basename)

    create_cp = False
    if basename in ["composite_traintuple", "aggregatetuple", "traintuple"]:
        if not orc_task["compute_plan_key"]:
            # Auto-create compute plan if not provided
            # Is it still relevant ?
            create_cp = True
            orc_task["compute_plan_key"] = str(uuid.uuid4())

    registered_cp_data = None
    with get_orchestrator_client(get_channel_name(request)) as client:
        if create_cp:
            registered_cp_data = client.register_compute_plan(
                args={
                    "key": orc_task["compute_plan_key"],
                    "tag": "",
                    "name": orc_task["compute_plan_key"],
                    "metadata": "",
                    "delete_intermediary_models": False,
                }
            )

        registered_tasks_data = client.register_tasks({"tasks": [orc_task]})

    return registered_cp_data, registered_tasks_data[0]


def create(request, basename, get_success_headers):
    """Create a new computetask.

    The workflow is composed of several steps:
    - Register asset in the orchestrator.
    - Save metadata in local database.
    """

    # Step1: register asset in orchestrator
    registered_cp_data, registered_task_data = _register_in_orchestrator(request, basename)

    # Step2: save metadata in local database
    if registered_cp_data is not None:
        registered_cp_data["channel"] = get_channel_name(request)
        localrep_cp_serializer = ComputePlanRepSerializer(data=registered_cp_data)
        try:
            localrep_cp_serializer.save_if_not_exists()
        except AlreadyExistsError:
            pass

    registered_task_data["channel"] = get_channel_name(request)
    localrep_task_serializer = ComputeTaskRepSerializer(data=registered_task_data)
    try:
        localrep_task_serializer.save_if_not_exists()
    except AlreadyExistsError:
        # May happen if the events app already processed the event pushed by the orchestrator
        compute_task = ComputeTaskRep.objects.get(key=registered_task_data["key"])
        localrep_task_data = ComputeTaskRepSerializer(compute_task).data
    else:
        localrep_task_data = localrep_task_serializer.data
    data = localrep_task_data

    # Return ApiResponse
    headers = get_success_headers(data)
    return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)


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
    filter_backends = (ComputePlanKeyOrderingFilter, CustomSearchFilter, MatchFilter, DjangoFilterBackend)
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
    ]
    ordering = ["creation_date", "key"]
    pagination_class = DefaultPageNumberPagination
    custom_search_mapping_callback = validate_status_and_map_cp_key  # deprecated
    search_fields = ("key",)
    filterset_class = ComputeTaskRepFilter

    @property
    def short_basename(self):
        return self.basename.removeprefix(CP_BASENAME_PREFIX)

    @property
    def category(self):
        return TASK_CATEGORY[self.short_basename]

    def get_custom_search_object_type(self):
        return self.short_basename

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ComputeTaskWithRelationshipsRepSerializer
        return ComputeTaskRepSerializer

    def get_queryset(self):
        queryset = ComputeTaskRep.objects.filter(
            channel=get_channel_name(self.request), category=self.category
        ).select_related("algo")
        if self.category == ComputeTaskRep.Category.TASK_TEST:
            queryset = queryset.prefetch_related("performances", "metrics")
        else:
            queryset = queryset.prefetch_related("models")
        return queryset


class ComputeTaskViewSet(
    ComputeTaskViewSetConfig, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet
):
    def create(self, request, *args, **kwargs):
        return create(request, self.short_basename, lambda data: self.get_success_headers(data))


class CPTaskViewSet(ComputeTaskViewSetConfig, mixins.ListModelMixin, GenericViewSet):
    def get_queryset(self):
        compute_plan_key = self.kwargs.get("compute_plan_pk")
        validate_key(compute_plan_key)

        queryset = super().get_queryset()
        return queryset.filter(compute_plan__key=compute_plan_key)

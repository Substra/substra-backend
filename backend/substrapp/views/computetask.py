import uuid

import structlog
from rest_framework import mixins
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

import orchestrator.computetask_pb2 as computetask_pb2
from libs.pagination import DefaultPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import ComputeTask as ComputeTaskRep
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from localrep.serializers import ComputeTaskWithRelationshipsSerializer as ComputeTaskWithRelationshipsRepSerializer
from substrapp.serializers import OrchestratorAggregateTaskSerializer
from substrapp.serializers import OrchestratorCompositeTrainTaskSerializer
from substrapp.serializers import OrchestratorTestTaskSerializer
from substrapp.serializers import OrchestratorTrainTaskSerializer
from substrapp.views.computeplan import register_compute_plan_in_orchestrator
from substrapp.views.filters_utils import CustomSearchFilter
from substrapp.views.utils import CP_BASENAME_PREFIX
from substrapp.views.utils import TASK_CATEGORY
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import MatchFilter
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import to_string_uuid
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


ORCHESTRATOR_SERIALIZER_CLASSES = {
    "traintuple": OrchestratorTrainTaskSerializer,
    "testtuple": OrchestratorTestTaskSerializer,
    "aggregatetuple": OrchestratorAggregateTaskSerializer,
    "composite_traintuple": OrchestratorCompositeTrainTaskSerializer,
}


def _register_in_orchestrator(request, basename):
    """Register computetask in orchestrator."""
    data = {
        "key": uuid.uuid4(),
        "category": TASK_CATEGORY[basename],
        "algo_key": request.data.get("algo_key"),
        "compute_plan_key": request.data.get("compute_plan_key"),
        "metadata": request.data.get("metadata"),
        "parent_task_keys": request.data.get("in_models_keys", []),
        "tag": request.data.get("tag", ""),
    }

    if basename == "composite_traintuple":
        data["data_manager_key"] = request.data.get("data_manager_key")
        data["data_sample_keys"] = request.data.get("train_data_sample_keys")
        data["trunk_permissions"] = request.data.get("out_trunk_model_permissions")
        # here we need to build a list from the head and trunk models sent by the user
        parent_task_keys = [request.data.get("in_head_model_key"), request.data.get("in_trunk_model_key")]
        data["parent_task_keys"] = [item for item in parent_task_keys if item]

    elif basename == "testtuple":
        data["metric_keys"] = request.data.get("metric_keys")
        data["data_manager_key"] = request.data.get("data_manager_key")
        data["data_sample_keys"] = request.data.get("test_data_sample_keys")

        if request.data.get("traintuple_key"):
            data["parent_task_keys"].append(request.data.get("traintuple_key"))
        else:
            raise ValidationExceptionError(
                data=[{"traintuple_key": ["This field may not be null."]}],
                key=data["key"],
                st=status.HTTP_400_BAD_REQUEST,
            )

        first_parent_task_id = to_string_uuid(data["parent_task_keys"][0])
        parent_task = ComputeTaskRep.objects.get(key=first_parent_task_id)
        data["algo_key"] = parent_task.algo.key
        data["compute_plan_key"] = parent_task.compute_plan.key

    elif basename == "aggregatetuple":
        data["worker"] = request.data.get("worker")

    elif basename == "traintuple":
        data["data_manager_key"] = request.data.get("data_manager_key")
        data["data_sample_keys"] = request.data.get("train_data_sample_keys")

    create_cp = False
    if basename in ["composite_traintuple", "aggregatetuple", "traintuple"]:
        if not data["compute_plan_key"]:
            # Auto-create compute plan if not provided
            # Is it still relevant ?
            create_cp = True
            data["compute_plan_key"] = uuid.uuid4()

    registered_cp_data = None
    if create_cp:
        registered_cp_data = register_compute_plan_in_orchestrator(request, data={"key": data["compute_plan_key"]})

    orchestrator_serializer_class = ORCHESTRATOR_SERIALIZER_CLASSES[basename]
    orchestrator_serializer = orchestrator_serializer_class(data=data, context={"request": request})
    orchestrator_serializer.is_valid(raise_exception=True)
    registered_tasks_data = orchestrator_serializer.create(
        get_channel_name(request), orchestrator_serializer.validated_data
    )
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


def map_status_and_cp_key(key, values):
    if key == "status":
        values = [computetask_pb2.ComputeTaskStatus.Value(value) for value in values]
    elif key == "compute_plan_key":
        key = "compute_plan_id"
    return key, values


class ComputePlanKeyOrderingFilter(OrderingFilter):
    """Allow ordering on compute_plan_key."""

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        return [v.replace("compute_plan_key", "compute_plan_id") for v in ordering]


class ComputeTaskViewSetConfig:
    serializer_class = ComputeTaskRepSerializer
    filter_backends = (ComputePlanKeyOrderingFilter, CustomSearchFilter, MatchFilter)
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
    custom_search_mapping_callback = map_status_and_cp_key
    search_fields = ("key",)

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
        if self.category == computetask_pb2.TASK_TEST:
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

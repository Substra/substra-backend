import uuid

import structlog
from django.urls import reverse
from rest_framework import mixins
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.viewsets import GenericViewSet

import orchestrator.computetask_pb2 as computetask_pb2
from libs.pagination import DefaultPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import ComputeTask as ComputeTaskRep
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from substrapp.compute_tasks.context import TASK_DATA_FIELD
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import OrchestratorAggregateTaskSerializer
from substrapp.serializers import OrchestratorCompositeTrainTaskSerializer
from substrapp.serializers import OrchestratorTestTaskSerializer
from substrapp.serializers import OrchestratorTrainTaskSerializer
from substrapp.views.computeplan import register_compute_plan_in_orchestrator
from substrapp.views.filters_utils import filter_queryset
from substrapp.views.utils import CP_BASENAME_PREFIX
from substrapp.views.utils import TASK_CATEGORY
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import add_task_extra_information
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import to_string_uuid
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


def replace_storage_addresses(request, task):
    # replace in common relationships

    if "algo" in task:
        task["algo"]["description"]["storage_address"] = request.build_absolute_uri(
            reverse("substrapp:algo-description", args=[task["algo"]["key"]])
        )
        task["algo"]["algorithm"]["storage_address"] = request.build_absolute_uri(
            reverse("substrapp:algo-file", args=[task["algo"]["key"]])
        )

    for parent_task in task.get("parent_tasks", []):
        replace_storage_addresses(request, parent_task)

    # replace in category-dependent relationships

    category = computetask_pb2.ComputeTaskCategory.Value(task["category"])
    task_details = task[TASK_DATA_FIELD[category]]

    if "data_manager" in task_details and task_details["data_manager"]:
        data_manager = task_details["data_manager"]
        data_manager["description"]["storage_address"] = request.build_absolute_uri(
            reverse("substrapp:data_manager-description", args=[data_manager["key"]])
        )
        data_manager["opener"]["storage_address"] = request.build_absolute_uri(
            reverse("substrapp:data_manager-opener", args=[data_manager["key"]])
        )

    models = task_details.get("models") or []  # field may be set to None
    for model in models:
        if "address" in model and model["address"]:
            model["address"]["storage_address"] = request.build_absolute_uri(
                reverse("substrapp:model-file", args=[model["key"]])
            )

    for metric in task_details.get("metrics", []):
        metric["description"]["storage_address"] = request.build_absolute_uri(
            reverse("substrapp:metric-description", args=[metric["key"]])
        )
        metric["address"]["storage_address"] = request.build_absolute_uri(
            reverse("substrapp:metric-metrics", args=[metric["key"]])
        )


class ComputeTaskListMixin:
    def list(self, request, compute_plan_pk=None):
        category = self.basename.removeprefix(CP_BASENAME_PREFIX)
        queryset = ComputeTaskRep.objects.filter(
            channel=get_channel_name(request),
            category=TASK_CATEGORY[category],
        ).order_by("creation_date", "key")

        if compute_plan_pk is not None:
            validated_key = validate_key(compute_plan_pk)
            queryset = queryset.filter(compute_plan__key=validated_key)

        query_params = request.query_params.get("search")
        if query_params is not None:

            def map_status_and_cp_key(key, values):
                if key == "status":
                    values = [computetask_pb2.ComputeTaskstatus.Value(value) for value in values]
                elif key == "compute_plan_key":
                    key = "compute_plan__key"
                return key, values

            queryset = filter_queryset(category, queryset, query_params, mapping_callback=map_status_and_cp_key)
        queryset = self.paginate_queryset(queryset)

        data = ComputeTaskRepSerializer(queryset, many=True).data
        for datum in data:
            with get_orchestrator_client(get_channel_name(request)) as client:
                datum = add_task_extra_information(client, category, datum, get_channel_name(request))
            replace_storage_addresses(request, datum)

        return self.get_paginated_response(data)


class CPTaskViewSet(ComputeTaskListMixin, GenericViewSet):
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return []


class ComputeTaskViewSet(ComputeTaskListMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_classes = {
        "traintuple": OrchestratorTrainTaskSerializer,
        "testtuple": OrchestratorTestTaskSerializer,
        "aggregatetuple": OrchestratorAggregateTaskSerializer,
        "composite_traintuple": OrchestratorCompositeTrainTaskSerializer,
    }
    pagination_class = DefaultPageNumberPagination

    def get_serializer_class(self):
        return self.serializer_classes[self.basename]

    def get_queryset(self):
        return []

    def _register_in_orchestrator(self, request):
        """Register computetask in orchestrator."""
        data = {
            "key": uuid.uuid4(),
            "category": TASK_CATEGORY[self.basename],
            "algo_key": request.data.get("algo_key"),
            "compute_plan_key": request.data.get("compute_plan_key"),
            "metadata": request.data.get("metadata"),
            "parent_task_keys": request.data.get("in_models_keys", []),
            "tag": request.data.get("tag", ""),
        }

        if self.basename == "composite_traintuple":
            data["data_manager_key"] = request.data.get("data_manager_key")
            data["data_sample_keys"] = request.data.get("train_data_sample_keys")
            data["trunk_permissions"] = request.data.get("out_trunk_model_permissions")
            # here we need to build a list from the head and trunk models sent by the user
            parent_task_keys = [request.data.get("in_head_model_key"), request.data.get("in_trunk_model_key")]
            data["parent_task_keys"] = [item for item in parent_task_keys if item]

        elif self.basename == "testtuple":
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

        elif self.basename == "aggregatetuple":
            data["worker"] = request.data.get("worker")

        elif self.basename == "traintuple":
            data["data_manager_key"] = request.data.get("data_manager_key")
            data["data_sample_keys"] = request.data.get("train_data_sample_keys")

        create_cp = False
        if self.basename in ["composite_traintuple", "aggregatetuple", "traintuple"]:
            if not data["compute_plan_key"]:
                # Auto-create compute plan if not provided
                # Is it still relevant ?
                create_cp = True
                data["compute_plan_key"] = uuid.uuid4()

        registered_cp_data = None
        if create_cp:
            registered_cp_data = register_compute_plan_in_orchestrator(request, data={"key": data["compute_plan_key"]})

        orchestrator_serializer = self.get_serializer(data=data, context={"request": request})
        orchestrator_serializer.is_valid(raise_exception=True)
        registered_tasks_data = orchestrator_serializer.create(
            get_channel_name(request), orchestrator_serializer.validated_data
        )
        return registered_cp_data, registered_tasks_data[0]

    def _create(self, request):  # noqa: C901
        """Create a new computetask.

        The workflow is composed of several steps:
        - Register asset in the orchestrator.
        - Save metadata in local database.
        """

        # Step1: register asset in orchestrator
        registered_cp_data, registered_task_data = self._register_in_orchestrator(request)

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

        return localrep_task_data

    def create(self, request, *args, **kwargs):
        data = self._create(request)
        headers = self.get_success_headers(data)
        return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)

    def _retrieve(self, request, key):
        validated_key = validate_key(key)
        try:
            compute_task = ComputeTaskRep.objects.filter(channel=get_channel_name(request)).get(key=validated_key)
        except ComputeTaskRep.DoesNotExist:
            raise NotFound
        data = ComputeTaskRepSerializer(compute_task).data

        with get_orchestrator_client(get_channel_name(request)) as client:
            data = add_task_extra_information(
                client, self.basename, data, get_channel_name(request), expand_relationships=True
            )

        replace_storage_addresses(request, data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        data = self._retrieve(request, key)
        return ApiResponse(data, status=status.HTTP_200_OK)

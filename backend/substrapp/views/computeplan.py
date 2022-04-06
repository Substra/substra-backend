import uuid

import structlog
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

import orchestrator.computeplan_pb2 as computeplan_pb2
from libs.pagination import DefaultPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import ComputePlan as ComputePlanRep
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import OrchestratorAggregateTaskSerializer
from substrapp.serializers import OrchestratorCompositeTrainTaskSerializer
from substrapp.serializers import OrchestratorTestTaskSerializer
from substrapp.serializers import OrchestratorTrainTaskSerializer
from substrapp.views.filters_utils import CustomSearchFilter
from substrapp.views.utils import TASK_CATEGORY
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import MatchFilter
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import to_string_uuid
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


def register_compute_plan_in_orchestrator(data, channel_name):

    orc_cp = {
        "key": str(data.get("key")),
        "tag": data.get("tag"),
        "metadata": data.get("metadata"),
        "delete_intermediary_models": data.get("delete_intermediary_models", False),
    }

    with get_orchestrator_client(channel_name) as client:
        return client.register_compute_plan(orc_cp)


def parse_traintuples(request, traintuples, compute_plan_key):
    tasks = {}
    for traintuple in traintuples:
        data = {
            "key": traintuple.get("traintuple_id"),
            "category": TASK_CATEGORY["traintuple"],
            "algo_key": traintuple.get("algo_key"),
            "compute_plan_key": compute_plan_key,
            "metadata": traintuple.get("metadata"),
            "parent_task_keys": traintuple.get("in_models_ids", []),
            "tag": traintuple.get("tag", ""),
            "data_manager_key": traintuple.get("data_manager_key"),
            "data_sample_keys": traintuple.get("train_data_sample_keys"),
        }
        orchestrator_serializer = OrchestratorTrainTaskSerializer(data=data, context={"request": request})

        try:
            orchestrator_serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

        task_data = orchestrator_serializer.get_args(orchestrator_serializer.validated_data)

        tasks[task_data["key"]] = task_data
    return tasks


def parse_composite_traintuple(request, composites, compute_plan_key):
    tasks = {}
    for composite in composites:
        parent_task_keys = [composite.get("in_head_model_id"), composite.get("in_trunk_model_id")]
        data = {
            "key": composite.get("composite_traintuple_id"),
            "category": TASK_CATEGORY["composite_traintuple"],
            "algo_key": composite.get("algo_key"),
            "compute_plan_key": compute_plan_key,
            "metadata": composite.get("metadata"),
            "parent_task_keys": [item for item in parent_task_keys if item],
            "tag": composite.get("tag", ""),
            "data_manager_key": composite.get("data_manager_key"),
            "data_sample_keys": composite.get("train_data_sample_keys"),
            "trunk_permissions": composite.get("out_trunk_model_permissions"),
        }

        orchestrator_serializer = OrchestratorCompositeTrainTaskSerializer(data=data, context={"request": request})

        try:
            orchestrator_serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

        task_data = orchestrator_serializer.get_args(orchestrator_serializer.validated_data)
        logger.debug(task_data)
        tasks[task_data["key"]] = task_data
    return tasks


def parse_aggregate_traintuple(request, aggregates, compute_plan_key):
    tasks = {}
    for aggregate in aggregates:
        data = {
            "key": aggregate.get("aggregatetuple_id"),
            "category": TASK_CATEGORY["aggregatetuple"],
            "algo_key": aggregate.get("algo_key"),
            "compute_plan_key": compute_plan_key,
            "metadata": aggregate.get("metadata"),
            "parent_task_keys": aggregate.get("in_models_ids", []),
            "tag": aggregate.get("tag", ""),
            "worker": aggregate.get("worker"),
        }

        orchestrator_serializer = OrchestratorAggregateTaskSerializer(data=data, context={"request": request})

        try:
            orchestrator_serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

        task_data = orchestrator_serializer.get_args(orchestrator_serializer.validated_data)

        tasks[task_data["key"]] = task_data
    return tasks


def parse_testtuple(request, testtuples, compute_plan_key, compute_tasks):
    tasks = {}
    for testtuple in testtuples:
        data = {
            "key": uuid.uuid4(),
            "category": TASK_CATEGORY["testtuple"],
            "compute_plan_key": compute_plan_key,
            "metadata": testtuple.get("metadata"),
            "tag": testtuple.get("tag", ""),
            "metric_keys": testtuple.get("metric_keys"),
            "data_manager_key": testtuple.get("data_manager_key"),
            "data_sample_keys": testtuple.get("test_data_sample_keys"),
            "parent_task_keys": [],
        }

        if testtuple.get("traintuple_id"):
            # This conversion is required to accept hex UUID format for the traintuple_id
            traintuple_id = to_string_uuid(testtuple.get("traintuple_id"))
            data["parent_task_keys"].append(traintuple_id)
            algo_key = compute_tasks.get(traintuple_id, {}).get("algo_key")
            if algo_key:
                data["algo_key"] = algo_key
            else:
                # The training task might already be registered and not part of the current batch
                with get_orchestrator_client(get_channel_name(request)) as client:
                    task = client.query_task(traintuple_id)
                    data["algo_key"] = task["algo"]["key"]
        else:
            raise ValidationExceptionError(
                data=[{"traintuple_id": ["This field may not be null."]}],
                key=data["key"],
                st=status.HTTP_400_BAD_REQUEST,
            )

        orchestrator_serializer = OrchestratorTestTaskSerializer(data=data, context={"request": request})

        try:
            orchestrator_serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

        task_data = orchestrator_serializer.get_args(orchestrator_serializer.validated_data)

        tasks[task_data["key"]] = task_data
    return tasks


def create(request, get_success_headers):
    """Create a new computeplan.

    The workflow is composed of several steps:
    - Register asset in the orchestrator.
    - Save metadata in local database.
    """
    # Step1: register asset in orchestrator
    compute_plan_data = {
        "key": uuid.uuid4(),
        "tag": request.data.get("tag"),
        "metadata": request.data.get("metadata"),
        "delete_intermediary_models": request.data.get("clean_models", False),
    }
    # To handle later
    traintuples = request.data.get("traintuples", [])
    validated_traintuples = parse_traintuples(request, traintuples, compute_plan_data["key"])
    composites = request.data.get("composite_traintuples", [])
    validated_composites = parse_composite_traintuple(request, composites, compute_plan_data["key"])
    aggregatetuples = request.data.get("aggregatetuples", [])
    validated_aggregates = parse_aggregate_traintuple(request, aggregatetuples, compute_plan_data["key"])
    testtuples = request.data.get("testtuples", [])
    validated_testtuples = parse_testtuple(
        request,
        testtuples,
        compute_plan_data["key"],
        {**validated_traintuples, **validated_composites, **validated_aggregates},
    )

    tasks = (
        list(validated_traintuples.values())
        + list(validated_composites.values())
        + list(validated_aggregates.values())
        + list(validated_testtuples.values())
    )

    localrep_data = register_compute_plan_in_orchestrator(compute_plan_data, get_channel_name(request))

    if tasks:
        with get_orchestrator_client(get_channel_name(request)) as client:
            registered_tasks_data = client.register_tasks({"tasks": tasks})

    # Step2: save metadata in local database
    localrep_data["channel"] = get_channel_name(request)
    localrep_serializer = ComputePlanRepSerializer(data=localrep_data)
    try:
        localrep_serializer.save_if_not_exists()
    except AlreadyExistsError:
        # May happen if the events app already processed the event pushed by the orchestrator
        cp = ComputePlanRep.objects.get(key=localrep_data["key"])
        data = ComputePlanRepSerializer(cp).data
    else:
        data = localrep_serializer.data

    # Save tasks metadata in localrep
    if tasks:
        for registered_task_data in registered_tasks_data:
            registered_task_data["channel"] = get_channel_name(request)
            task_serializer = ComputeTaskRepSerializer(data=registered_task_data)
            try:
                task_serializer.save_if_not_exists()
            except AlreadyExistsError:
                # May happen if the events app already processed the event pushed by the orchestrator
                pass

    # Return ApiResponse
    headers = get_success_headers(data)
    return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)


def map_status(key, values):
    if key == "status":
        values = [computeplan_pb2.ComputePlanStatus.Value(value) for value in values]
    return key, values


class MetadataOrderingFilter(OrderingFilter):
    """Allows ordering on any metadata value."""

    def remove_invalid_fields(self, queryset, fields, view, request):
        # This method considers all fields starting with metadata__ as valid fields.
        # This is because adding "metadata" to the ordering_fields conf doesn't automatically
        # allows filtering on metadata subvalues
        valid_fields = [item[0] for item in self.get_valid_fields(queryset, view, {"request": request})]

        def term_valid(term):
            if term.startswith("-"):
                term = term[1:]
            return term in valid_fields or term.startswith("metadata__")

        return [term for term in fields if term_valid(term)]


class ComputePlanViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = ComputePlanRepSerializer
    pagination_class = DefaultPageNumberPagination
    filter_backends = (MetadataOrderingFilter, CustomSearchFilter, MatchFilter)
    ordering_fields = ["creation_date", "start_date", "end_date", "key", "owner", "status", "tag"]
    custom_search_object_type = "compute_plan"
    custom_search_mapping_callback = map_status
    search_fields = ("key", "metadata__name")

    def get_queryset(self):
        return ComputePlanRep.objects.filter(channel=get_channel_name(self.request))

    def create(self, request, *args, **kwargs):
        return create(request, lambda data: self.get_success_headers(data))

    @action(detail=True, methods=["POST"])
    def cancel(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        validated_key = validate_key(key)

        with get_orchestrator_client(get_channel_name(request)) as client:
            client.cancel_compute_plan(key)
            compute_plan = client.query_compute_plan(validated_key)

        return ApiResponse(compute_plan, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def update_ledger(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        validated_key = validate_key(key)

        traintuples = request.data.get("traintuples", [])
        validated_traintuples = parse_traintuples(request, traintuples, validated_key)
        composites = request.data.get("composite_traintuples", [])
        validated_composites = parse_composite_traintuple(request, composites, validated_key)
        aggregatetuples = request.data.get("aggregatetuples", [])
        validated_aggregates = parse_aggregate_traintuple(request, aggregatetuples, validated_key)
        testtuples = request.data.get("testtuples", [])
        validated_testtuples = parse_testtuple(
            request,
            testtuples,
            validated_key,
            {**validated_traintuples, **validated_composites, **validated_aggregates},
        )

        tasks = (
            list(validated_traintuples.values())
            + list(validated_composites.values())
            + list(validated_aggregates.values())
            + list(validated_testtuples.values())
        )

        with get_orchestrator_client(get_channel_name(request)) as client:
            registered_tasks_data = client.register_tasks({"tasks": tasks})

        # Save tasks metadata in localrep
        for registered_task_data in registered_tasks_data:
            registered_task_data["channel"] = get_channel_name(request)
            task_serializer = ComputeTaskRepSerializer(data=registered_task_data)
            try:
                task_serializer.save_if_not_exists()
            except AlreadyExistsError:
                # May happen if the events app already processed the event pushed by the orchestrator
                pass

        # Update cp status after creating tasks

        compute_plan = ComputePlanRep.objects.get(key=validated_key)
        compute_plan.update_status()

        return ApiResponse({}, status=status.HTTP_200_OK)

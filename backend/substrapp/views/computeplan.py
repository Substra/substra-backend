import uuid

import structlog
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.viewsets import GenericViewSet

from libs.pagination import DefaultPageNumberPagination
from libs.pagination import PaginationMixin
from localrep.errors import AlreadyExistsError
from localrep.models import ComputePlan as ComputePlanRep
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import OrchestratorAggregateTaskSerializer
from substrapp.serializers import OrchestratorCompositeTrainTaskSerializer
from substrapp.serializers import OrchestratorComputePlanSerializer
from substrapp.serializers import OrchestratorTestTaskSerializer
from substrapp.serializers import OrchestratorTrainTaskSerializer
from substrapp.views.filters_utils import filter_list
from substrapp.views.filters_utils import filter_queryset
from substrapp.views.utils import TASK_CATEGORY
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import add_compute_plan_duration_or_eta
from substrapp.views.utils import add_compute_plan_failed_task
from substrapp.views.utils import add_cp_status_and_task_counts
from substrapp.views.utils import add_task_extra_information
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import to_string_uuid
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


def register_compute_plan_in_orchestrator(request, data):
    serializer = OrchestratorComputePlanSerializer(data=data, context={"request": request})
    try:
        serializer.is_valid(raise_exception=True)
    except Exception as e:
        raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)
    return serializer.create(get_channel_name(request), serializer.validated_data)


BASENAME_PREFIX = "compute_plan_"


class ComputePlanViewSet(mixins.CreateModelMixin, GenericViewSet):

    serializer_class = OrchestratorComputePlanSerializer
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return []

    def parse_traintuples(self, request, traintuples, compute_plan_key):
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

    def parse_composite_traintuple(self, request, composites, compute_plan_key):
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

    def parse_aggregate_traintuple(self, request, aggregates, compute_plan_key):
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

    def parse_testtuple(self, request, testtuples, compute_plan_key, compute_tasks):
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

    def create(self, request, *args, **kwargs):
        data = self._create(request)
        headers = self.get_success_headers(data)
        return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)

    def _create(self, request):
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
        validated_traintuples = self.parse_traintuples(request, traintuples, compute_plan_data["key"])
        composites = request.data.get("composite_traintuples", [])
        validated_composites = self.parse_composite_traintuple(request, composites, compute_plan_data["key"])
        aggregatetuples = request.data.get("aggregatetuples", [])
        validated_aggregates = self.parse_aggregate_traintuple(request, aggregatetuples, compute_plan_data["key"])
        testtuples = request.data.get("testtuples", [])
        validated_testtuples = self.parse_testtuple(
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

        localrep_data = register_compute_plan_in_orchestrator(request, data=compute_plan_data)

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

        data = add_cp_status_and_task_counts(data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        validated_key = validate_key(key)

        try:
            compute_plan = ComputePlanRep.objects.get(key=validated_key)
        except ComputePlanRep.DoesNotExist:
            raise NotFound
        data = ComputePlanRepSerializer(compute_plan).data
        data = add_cp_status_and_task_counts(data)

        with get_orchestrator_client(get_channel_name(request)) as client:
            data = add_compute_plan_failed_task(client, data)
            data = add_compute_plan_duration_or_eta(client, data)

        return ApiResponse(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = ComputePlanRep.objects.filter(channel=get_channel_name(request))

        query_params = request.query_params.get("search")
        if query_params is not None:
            queryset = filter_queryset("compute_plan", queryset, query_params)
        queryset = self.paginate_queryset(queryset)

        data = ComputePlanRepSerializer(queryset, many=True).data

        with get_orchestrator_client(get_channel_name(request)) as client:
            for datum in data:
                datum = add_cp_status_and_task_counts(datum)
                datum = add_compute_plan_duration_or_eta(client, datum)

        return self.get_paginated_response(data)

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
        validated_traintuples = self.parse_traintuples(request, traintuples, validated_key)
        composites = request.data.get("composite_traintuples", [])
        validated_composites = self.parse_composite_traintuple(request, composites, validated_key)
        aggregatetuples = request.data.get("aggregatetuples", [])
        validated_aggregates = self.parse_aggregate_traintuple(request, aggregatetuples, validated_key)
        testtuples = request.data.get("testtuples", [])
        validated_testtuples = self.parse_testtuple(
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

        return ApiResponse({}, status=status.HTTP_200_OK)


class GenericSubassetViewset(PaginationMixin, GenericViewSet):

    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return []

    def list(self, request, compute_plan_pk):
        if not self.is_page_size_param_present():
            # We choose to force the page_size parameter in these views in order to limit the number of queries
            # to the chaincode
            return ApiResponse(status=status.HTTP_400_BAD_REQUEST, data="page_size param is required")

        validated_key = validate_key(compute_plan_pk)
        truncated_basename = self.basename.removeprefix(BASENAME_PREFIX)

        with get_orchestrator_client(get_channel_name(request)) as client:
            search_params = request.query_params.get("search")
            data = self._fetch_data(client, validated_key, truncated_basename, search_params)

        return self.paginate_response(data)

    def _filter_data(self, data, search_params, truncated_basename):
        if search_params is None:
            return data
        return filter_list(
            object_type=truncated_basename,
            data=data,
            query_params=search_params,
        )


class CPTaskViewSet(GenericSubassetViewset):
    def _fetch_data(self, client, compute_plan_pk, truncated_basename, search_params):
        category = TASK_CATEGORY[truncated_basename]
        data = client.query_tasks(category=category, compute_plan_key=compute_plan_pk)
        data = self._filter_data(data, search_params, truncated_basename)

        for datum in data:
            datum = add_task_extra_information(client, truncated_basename, datum)
        return data


class CPAlgoViewSet(GenericSubassetViewset):
    # return all algos related to a specific CP
    def _fetch_data(self, client, compute_plan_pk, truncated_basename, search_params):
        validated_key = validate_key(compute_plan_pk)
        data = client.query_algos(compute_plan_key=validated_key)
        data = self._filter_data(data, search_params, truncated_basename)

        return data

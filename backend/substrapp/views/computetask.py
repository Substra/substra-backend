import uuid

import structlog
from django.urls import reverse
from rest_framework import mixins
from rest_framework import status
from rest_framework.viewsets import GenericViewSet

import orchestrator.computetask_pb2 as computetask_pb2
from libs.pagination import DefaultPageNumberPagination
from libs.pagination import PaginationMixin
from substrapp.compute_tasks.context import TASK_DATA_FIELD
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import OrchestratorAggregateTaskSerializer
from substrapp.serializers import OrchestratorCompositeTrainTaskSerializer
from substrapp.serializers import OrchestratorTestTaskSerializer
from substrapp.serializers import OrchestratorTrainTaskSerializer
from substrapp.views.computeplan import create_compute_plan
from substrapp.views.filters_utils import filter_list
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


class ComputeTaskViewSet(mixins.CreateModelMixin, PaginationMixin, GenericViewSet):
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

    # TODO: 'commit' is too complex, consider refactoring
    def commit(self, request):  # noqa: C901
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

            with get_orchestrator_client(get_channel_name(request)) as client:
                first_parent_task_id = to_string_uuid(data["parent_task_keys"][0])
                parent_task = client.query_task(first_parent_task_id)
                data["algo_key"] = parent_task["algo"]["key"]
                data["compute_plan_key"] = parent_task["compute_plan_key"]

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

        orchestrator_serializer = self.get_serializer(data=data, context={"request": request})

        try:
            orchestrator_serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

        if create_cp:
            create_compute_plan(request, data={"key": data["compute_plan_key"]})

        # create on orchestrator db
        data = orchestrator_serializer.create(get_channel_name(request), orchestrator_serializer.validated_data)

        merged_data = dict(orchestrator_serializer.data)
        merged_data.update(data)

        return merged_data

    def create(self, request, *args, **kwargs):
        data = self.commit(request)
        headers = self.get_success_headers(data)
        return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        with get_orchestrator_client(get_channel_name(request)) as client:
            data = client.query_tasks(category=TASK_CATEGORY[self.basename])

        query_params = request.query_params.get("search")
        if query_params is not None:
            data = filter_list(object_type=self.basename, data=data, query_params=query_params)

        with get_orchestrator_client(get_channel_name(request)) as client:
            for datum in data:
                datum = add_task_extra_information(client, self.basename, datum)

        for task in data:
            replace_storage_addresses(request, task)

        return self.paginate_response(data)

    def _retrieve(self, request, key):
        validated_key = validate_key(key)
        with get_orchestrator_client(get_channel_name(request)) as client:
            data = client.query_task(validated_key)
            data = add_task_extra_information(client, self.basename, data, expand_relationships=True)

        replace_storage_addresses(request, data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        data = self._retrieve(request, key)
        return ApiResponse(data, status=status.HTTP_200_OK)

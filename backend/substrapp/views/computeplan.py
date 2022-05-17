import structlog
from django.db import models
from django_filters.rest_framework import BaseInFilter
from django_filters.rest_framework import DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

from libs.pagination import SmallPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import ComputePlan as ComputePlanRep
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from substrapp import exceptions
from substrapp.orchestrator import get_orchestrator_client
from substrapp.views.computetask import build_computetask_data
from substrapp.views.filters_utils import CustomSearchFilter
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import ChoiceInFilter
from substrapp.views.utils import MatchFilter
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import to_string_uuid
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


def register_compute_plan_in_orchestrator(data, channel_name):

    orc_cp = {
        "key": str(data.get("key")),
        "tag": data.get("tag"),
        "name": data.get("name"),
        "metadata": data.get("metadata"),
        "delete_intermediary_models": data.get("delete_intermediary_models", False),
    }

    with get_orchestrator_client(channel_name) as client:
        return client.register_compute_plan(orc_cp)


def extract_tasks_data(data, compute_plan_key):

    task_pairs = [
        ("traintuple", "traintuples"),
        ("composite_traintuple", "composite_traintuples"),
        ("aggregatetuple", "aggregatetuples"),
        ("testtuple", "testtuples"),
    ]

    extracted_tasks = {
        "traintuple": {},
        "composite_traintuple": {},
        "aggregatetuple": {},
        "testtuple": {},
    }

    for task_type, task_data_attribute in task_pairs:
        for task in data.get(task_data_attribute, []):

            if task_type == "testtuple":
                tasks_cache = {
                    **extracted_tasks["traintuple"],
                    **extracted_tasks["composite_traintuple"],
                    **extracted_tasks["aggregatetuple"],
                }
            else:
                tasks_cache = None

            task_data = build_computetask_data(
                {**task, **{"compute_plan_key": compute_plan_key}},
                task_type,
                tasks_cache=tasks_cache,
                from_compute_plan=True,
            )
            extracted_tasks[task_type][task_data["key"]] = task_data

    return (
        list(extracted_tasks["traintuple"].values())
        + list(extracted_tasks["composite_traintuple"].values())
        + list(extracted_tasks["aggregatetuple"].values())
        + list(extracted_tasks["testtuple"].values())
    )


def create(request, get_success_headers):
    """Create a new computeplan.

    The workflow is composed of several steps:
    - Register asset in the orchestrator.
    - Save metadata in local database.
    """
    # Step1: register asset in orchestrator
    compute_plan_data = {
        "key": to_string_uuid(request.data.get("key")),
        "tag": request.data.get("tag"),
        "name": request.data.get("name"),
        "metadata": request.data.get("metadata"),
        "delete_intermediary_models": request.data.get("clean_models", False),
    }

    tasks = extract_tasks_data(request.data, str(compute_plan_data["key"]))

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


def validate_status(key, values):
    if key == "status":
        try:
            for value in values:
                getattr(ComputePlanRep.Status, value)
        except AttributeError as e:
            raise exceptions.BadRequestError(f"Wrong {key} value: {e}")
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


class ComputePlanRepFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter()
    start_date = DateTimeFromToRangeFilter()
    end_date = DateTimeFromToRangeFilter()
    status = ChoiceInFilter(
        field_name="status",
        choices=ComputePlanRep.Status.choices,
    )

    class Meta:
        model = ComputePlanRep
        fields = {
            "owner": ["exact"],
            "key": ["exact"],
            "tag": ["exact"],
            "name": ["exact"],
        }
        filter_overrides = {
            models.CharField: {
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


class ComputePlanViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = ComputePlanRepSerializer
    pagination_class = SmallPageNumberPagination
    filter_backends = (MetadataOrderingFilter, CustomSearchFilter, MatchFilter, DjangoFilterBackend)
    ordering_fields = ["creation_date", "start_date", "end_date", "key", "owner", "status", "tag", "name"]
    custom_search_object_type = "compute_plan"  # deprecated
    custom_search_mapping_callback = validate_status  # deprecated
    search_fields = ("key", "name")
    filterset_class = ComputePlanRepFilter

    def get_queryset(self):
        return ComputePlanRep.objects.filter(channel=get_channel_name(self.request))

    def create(self, request, *args, **kwargs):
        return create(request, lambda data: self.get_success_headers(data))

    @action(detail=True, methods=["POST"])
    def cancel(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        with get_orchestrator_client(get_channel_name(request)) as client:
            client.cancel_compute_plan(key)
        return ApiResponse({}, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def update_ledger(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        validated_key = validate_key(key)

        tasks = extract_tasks_data(request.data, str(validated_key))

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

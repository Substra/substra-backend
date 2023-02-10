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
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

from api.errors import AlreadyExistsError
from api.errors import BadRequestError
from api.models import ComputePlan
from api.serializers import ComputePlanSerializer
from api.views.filters_utils import CharInFilter
from api.views.filters_utils import ChoiceInFilter
from api.views.filters_utils import MatchFilter
from api.views.filters_utils import MetadataFilterBackend
from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from api.views.utils import to_string_uuid
from api.views.utils import validate_metadata
from libs.pagination import SmallPageNumberPagination
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger(__name__)


def _register_in_orchestrator(data, channel_name):
    """Register computeplan in orchestrator."""

    orc_cp = {
        "key": str(data.get("key")),
        "tag": data.get("tag"),
        "name": data.get("name"),
        "metadata": data.get("metadata"),
    }
    with get_orchestrator_client(channel_name) as client:
        return client.register_compute_plan(orc_cp)


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
        "metadata": validate_metadata(request.data.get("metadata")),
    }
    api_data = _register_in_orchestrator(compute_plan_data, get_channel_name(request))

    # Step2: save metadata in local database
    api_data["channel"] = get_channel_name(request)
    api_data["creator"] = request.user.id

    api_serializer = ComputePlanSerializer(data=api_data)
    try:
        api_serializer.save_if_not_exists()
    except AlreadyExistsError:
        # May happen if the events app already processed the event pushed by the orchestrator
        # In that case, set creator as from event it is always assumed to be an external creator
        cp = ComputePlan.objects.get(key=api_data["key"])
        serializer = ComputePlanSerializer(cp, data={"creator": request.user.id}, partial=True)
        if serializer.is_valid():
            serializer.save()
        data = serializer.data
    else:
        data = api_serializer.data

    # Return ApiResponse
    headers = get_success_headers(data)
    return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)


def validate_status(key, values):
    if key == "status":
        try:
            for value in values:
                getattr(ComputePlan.Status, value)
        except AttributeError as e:
            raise BadRequestError(f"Wrong {key} value: {e}")
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


class ComputePlanFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter()
    start_date = DateTimeFromToRangeFilter()
    end_date = DateTimeFromToRangeFilter()
    status = ChoiceInFilter(
        field_name="status",
        choices=ComputePlan.Status.choices,
    )
    function_key = CharFilter(field_name="compute_tasks__function__key", distinct=True, label="function_key")
    dataset_key = CharFilter(field_name="compute_tasks__data_manager__key", distinct=True, label="dataset_key")
    data_sample_key = CharInFilter(
        field_name="compute_tasks__data_samples__key", distinct=True, label="data_sample_key"
    )
    duration = RangeFilter(label="duration")
    creator = CharFilter(field_name="creator__username", label="creator")

    class Meta:
        model = ComputePlan
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


class ComputePlanMetadataFilter(MetadataFilterBackend):
    def _apply_filters(self, queryset, filter_keys):
        return queryset.annotate(
            metadata_filters=JSONObject(
                **{
                    f"{filter_key}": RawSQL(
                        "api_computeplan.metadata ->> %s",
                        (filter_key,),
                    )
                    for filter_key in filter_keys
                }
            )
        )


class ComputePlanViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = ComputePlanSerializer
    pagination_class = SmallPageNumberPagination
    filter_backends = (
        MetadataOrderingFilter,
        MatchFilter,
        DjangoFilterBackend,
        ComputePlanMetadataFilter,
    )
    ordering_fields = [
        "creation_date",
        "start_date",
        "end_date",
        "key",
        "owner",
        "status",
        "tag",
        "name",
        "duration",
        "creator",
    ]
    search_fields = ("key", "name")
    filterset_class = ComputePlanFilter

    def get_queryset(self):
        return ComputePlan.objects.filter(channel=get_channel_name(self.request)).annotate(
            # Using 0 as default value instead of None for ordering purpose, as default
            # Postgres behavior considers null as greater than any other value.
            duration=models.Case(
                models.When(start_date__isnull=True, then=0),
                default=Extract(Coalesce("end_date", Now()) - models.F("start_date"), "epoch"),
            ),
        )

    def create(self, request, *args, **kwargs):
        return create(request, lambda data: self.get_success_headers(data))

    def update(self, request, *args, **kwargs):
        compute_plan = self.get_object()
        name = request.data.get("name")

        orc_compute_plan = {
            "key": str(compute_plan.key),
            "name": name,
        }

        # send update to orchestrator
        # the modification in local db will be done upon corresponding event reception
        with get_orchestrator_client(get_channel_name(request)) as client:
            client.update_compute_plan(orc_compute_plan)

        return ApiResponse({}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"])
    def cancel(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        with get_orchestrator_client(get_channel_name(request)) as client:
            client.cancel_compute_plan(key)
        return ApiResponse({}, status=status.HTTP_200_OK)

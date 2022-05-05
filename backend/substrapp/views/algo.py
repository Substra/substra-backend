import structlog
from django.conf import settings
from django.db import models
from django.urls import reverse
from django_filters.rest_framework import BaseInFilter
from django_filters.rest_framework import DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

import orchestrator.algo_pb2 as algo_pb2
from libs.pagination import DefaultPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import Algo as AlgoRep
from localrep.serializers import AlgoSerializer as AlgoRepSerializer
from orchestrator.algo_pb2 import AlgoCategory
from orchestrator.algo_pb2 import AlgoInput
from orchestrator.algo_pb2 import AlgoOutput
from orchestrator.common_pb2 import AssetKind
from substrapp import exceptions
from substrapp.models import Algo
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import AlgoSerializer
from substrapp.utils import get_hash
from substrapp.views.filters_utils import CustomSearchFilter
from substrapp.views.utils import CP_BASENAME_PREFIX
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import MatchFilter
from substrapp.views.utils import PermissionMixin
from substrapp.views.utils import TypedChoiceInFilter
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)

# This mapping will be deleted once the algo inputs are provided by the client
ALGO_INPUTS_PER_CATEGORY = {
    AlgoCategory.ALGO_SIMPLE: {
        "opener": AlgoInput(kind=AssetKind.ASSET_DATA_MANAGER),
        "datasamples": AlgoInput(kind=AssetKind.ASSET_DATA_SAMPLE, multiple=True),
        "model": AlgoInput(kind=AssetKind.ASSET_MODEL, optional=True),
    },
    AlgoCategory.ALGO_COMPOSITE: {
        "opener": AlgoInput(kind=AssetKind.ASSET_DATA_MANAGER),
        "data-samples": AlgoInput(kind=AssetKind.ASSET_DATA_SAMPLE, multiple=True),
        "shared": AlgoInput(kind=AssetKind.ASSET_MODEL, optional=True),
        "local": AlgoInput(kind=AssetKind.ASSET_MODEL, optional=True),
    },
    AlgoCategory.ALGO_AGGREGATE: {
        "model": AlgoInput(kind=AssetKind.ASSET_MODEL, multiple=True),
    },
    AlgoCategory.ALGO_METRIC: {  # evaluation step
        "opener": AlgoInput(kind=AssetKind.ASSET_DATA_MANAGER),
        "data-samples": AlgoInput(kind=AssetKind.ASSET_DATA_SAMPLE, multiple=True),
        # we don't have a "predictions" asset kind yet, so we use the "model" kind
        "predictions": AlgoInput(kind=AssetKind.ASSET_MODEL, optional=True),
    },
    # Note: algo of category "prediction" is missing. This will becomes irrelevant once we get rid of algo categories
    # and inputs are provided by the client.
}

# This mapping will be deleted once the algo outputs are provided by the client
ALGO_OUTPUTS_PER_CATEGORY = {
    AlgoCategory.ALGO_SIMPLE: {
        "model": AlgoOutput(kind=AssetKind.ASSET_MODEL),
    },
    AlgoCategory.ALGO_COMPOSITE: {
        "shared": AlgoOutput(kind=AssetKind.ASSET_MODEL),
        "local": AlgoOutput(kind=AssetKind.ASSET_MODEL),
    },
    AlgoCategory.ALGO_AGGREGATE: {
        "model": AlgoOutput(kind=AssetKind.ASSET_MODEL),
    },
    AlgoCategory.ALGO_METRIC: {  # evaluation step
        "performance": AlgoOutput(kind=AssetKind.ASSET_PERFORMANCE),
    },
    # Note: algo of category "prediction" is missing. This will becomes irrelevant once we get rid of algo categories
    # and inputs are provided by the client.
}


ALGO_CATEGORIES = {
    "algo": [
        algo_pb2.AlgoCategory.ALGO_UNKNOWN,
        algo_pb2.AlgoCategory.ALGO_SIMPLE,
        algo_pb2.AlgoCategory.ALGO_AGGREGATE,
        algo_pb2.AlgoCategory.ALGO_COMPOSITE,
    ],
    "metric": [algo_pb2.AlgoCategory.ALGO_METRIC],
}


def _register_in_orchestrator(request, basename, instance):
    """Register algo in orchestrator."""

    if basename == "metric":
        category = algo_pb2.AlgoCategory.ALGO_METRIC
    else:
        try:
            category = algo_pb2.AlgoCategory.Value(request.data.get("category"))
        except ValueError:
            raise ValidationError({"category": "Invalid category"})

    current_site = settings.DEFAULT_DOMAIN
    permissions = request.data.get("permissions", {})

    orc_algo = {
        "key": str(instance.key),
        "name": request.data.get("name"),
        "category": category,
        "description": {
            "checksum": get_hash(instance.description),
            "storage_address": current_site + reverse("substrapp:algo-description", args=[instance.key]),
        },
        "algorithm": {
            "checksum": instance.checksum,
            "storage_address": current_site + reverse("substrapp:algo-file", args=[instance.key]),
        },
        "new_permissions": {
            "public": permissions.get("public"),
            "authorized_ids": permissions.get("authorized_ids"),
        },
        "metadata": request.data.get("metadata"),
        "inputs": ALGO_INPUTS_PER_CATEGORY[category],
        "outputs": ALGO_OUTPUTS_PER_CATEGORY[category],
    }

    with get_orchestrator_client(get_channel_name(request)) as client:
        return client.register_algo(orc_algo)


def create(request, basename, get_success_headers):
    """Create a new algo.

    The workflow is composed of several steps:
    - Save files in local database to get the addresses.
    - Register asset in the orchestrator.
    - Save metadata in local database.
    """
    # Step1: save files in local database
    file = request.data.get("file")
    try:
        checksum = get_hash(file)
    except Exception as e:
        raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

    serializer = AlgoSerializer(
        data={"file": file, "description": request.data.get("description"), "checksum": checksum}
    )

    try:
        serializer.is_valid(raise_exception=True)
    except Exception as e:
        raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

    instance = serializer.save()

    # Step2: register asset in orchestrator
    try:
        localrep_data = _register_in_orchestrator(request, basename, instance)
    except Exception:
        instance.delete()  # warning: post delete signals are not executed by django rollback
        raise

    # Step3: save metadata in local database
    localrep_data["channel"] = get_channel_name(request)
    localrep_serializer = AlgoRepSerializer(data=localrep_data)
    try:
        localrep_serializer.save_if_not_exists()
    except AlreadyExistsError:
        # May happen if the events app already processed the event pushed by the orchestrator
        algo = AlgoRep.objects.get(key=localrep_data["key"])
        data = AlgoRepSerializer(algo).data
    except Exception:
        instance.delete()  # warning: post delete signals are not executed by django rollback
        raise
    else:
        data = localrep_serializer.data

    # Returns algo metadata from local database (and algo data) to ensure consistency between GET and CREATE views
    data.update(serializer.data)

    # Return ApiResponse
    headers = get_success_headers(data)
    return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)


def map_category(key, values):
    if key == "category":
        try:
            values = [algo_pb2.AlgoCategory.Value(value) for value in values]
        except ValueError as e:
            raise exceptions.BadRequestError(f"Wrong {key} value: {e}")
    return key, values


class AlgoRepFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter()
    category = TypedChoiceInFilter(
        field_name="category",
        choices=[(key, key) for key in algo_pb2.AlgoCategory.keys()],
        coerce=lambda x: algo_pb2.AlgoCategory.Value(x),
    )

    class Meta:
        model = AlgoRep
        fields = {
            "owner": ["exact"],
            "key": ["exact"],
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


class AlgoViewSetConfig:
    serializer_class = AlgoRepSerializer
    filter_backends = (OrderingFilter, CustomSearchFilter, MatchFilter, DjangoFilterBackend)
    ordering_fields = ["creation_date", "key", "name", "owner", "category"]
    ordering = ["creation_date", "key"]
    pagination_class = DefaultPageNumberPagination
    custom_search_object_type = "algo"
    custom_search_mapping_callback = map_category
    filterset_class = AlgoRepFilter

    @property
    def categories(self):
        return ALGO_CATEGORIES[self.basename.removeprefix(CP_BASENAME_PREFIX)]

    def get_queryset(self):
        return AlgoRep.objects.filter(channel=get_channel_name(self.request), category__in=self.categories)


class AlgoViewSet(
    AlgoViewSetConfig, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet
):
    def create(self, request, *args, **kwargs):
        return create(request, self.basename, lambda data: self.get_success_headers(data))


class CPAlgoViewSet(AlgoViewSetConfig, mixins.ListModelMixin, GenericViewSet):
    def get_queryset(self):
        compute_plan_key = self.kwargs.get("compute_plan_pk")
        validate_key(compute_plan_key)
        queryset = super().get_queryset()
        return queryset.filter(compute_tasks__compute_plan__key=compute_plan_key).distinct()


class AlgoPermissionViewSet(PermissionMixin, GenericViewSet):
    queryset = Algo.objects.all()
    serializer_class = AlgoSerializer

    @action(detail=True)
    def file(self, request, *args, **kwargs):
        return self.download_file(request, AlgoRep, "file", "algorithm_address")

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions
    @action(detail=True, url_path="description", url_name="description")
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, AlgoRep, "description", "description_address")

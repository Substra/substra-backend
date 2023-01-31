import structlog
from django.conf import settings
from django.db import models
from django.urls import reverse
from django_filters.rest_framework import BaseInFilter
from django_filters.rest_framework import CharFilter
from django_filters.rest_framework import DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

from api.errors import AlreadyExistsError
from api.models import Algo
from api.serializers import AlgoSerializer
from api.views.filters_utils import CharInFilter
from api.views.filters_utils import MatchFilter
from api.views.filters_utils import ProcessPermissionFilter
from api.views.utils import ApiResponse
from api.views.utils import PermissionMixin
from api.views.utils import ValidationExceptionError
from api.views.utils import get_channel_name
from api.views.utils import validate_key
from api.views.utils import validate_metadata
from libs.pagination import DefaultPageNumberPagination
from substrapp.models import Algo as AlgoFiles
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import AlgoSerializer as AlgoFilesSerializer
from substrapp.utils import get_hash

logger = structlog.get_logger(__name__)


def _register_in_orchestrator(request, basename, instance):
    """Register function in orchestrator."""

    current_site = settings.DEFAULT_DOMAIN
    permissions = request.data.get("permissions", {})

    orc_algo = {
        "key": str(instance.key),
        "name": request.data.get("name"),
        "description": {
            "checksum": get_hash(instance.description),
            "storage_address": current_site + reverse("api:function-description", args=[instance.key]),
        },
        "algorithm": {
            "checksum": instance.checksum,
            "storage_address": current_site + reverse("api:function-file", args=[instance.key]),
        },
        "new_permissions": {
            "public": permissions.get("public"),
            "authorized_ids": permissions.get("authorized_ids"),
        },
        "metadata": validate_metadata(request.data.get("metadata")),
        "inputs": request.data["inputs"],
        "outputs": request.data["outputs"],
    }

    with get_orchestrator_client(get_channel_name(request)) as client:
        return client.register_algo(orc_algo)


def create(request, basename, get_success_headers):
    """Create a new function.

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

    serializer = AlgoFilesSerializer(
        data={"file": file, "description": request.data.get("description"), "checksum": checksum}
    )

    try:
        serializer.is_valid(raise_exception=True)
    except Exception as e:
        raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

    instance = serializer.save()

    # Step2: register asset in orchestrator
    try:
        api_data = _register_in_orchestrator(request, basename, instance)
    except Exception:
        instance.delete()  # warning: post delete signals are not executed by django rollback
        raise

    # Step3: save metadata in local database
    api_data["channel"] = get_channel_name(request)
    api_serializer = AlgoSerializer(data=api_data)
    try:
        api_serializer.save_if_not_exists()
    except AlreadyExistsError:
        # May happen if the events app already processed the event pushed by the orchestrator
        function = Algo.objects.get(key=api_data["key"])
        data = AlgoSerializer(function).data
    except Exception:
        instance.delete()  # warning: post delete signals are not executed by django rollback
        raise
    else:
        data = api_serializer.data

    # Returns function metadata from local database (and function data)
    # to ensure consistency between GET and CREATE views
    data.update(serializer.data)

    # Return ApiResponse
    headers = get_success_headers(data)
    return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)


class AlgoFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter()

    compute_plan_key = CharInFilter(field_name="compute_tasks__compute_plan__key", label="compute_plan_key")
    dataset_key = CharFilter(field_name="compute_tasks__data_manager__key", distinct=True, label="dataset_key")
    data_sample_key = CharInFilter(
        field_name="compute_tasks__data_samples__key", distinct=True, label="data_sample_key"
    )

    class Meta:
        model = Algo
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
    serializer_class = AlgoSerializer
    filter_backends = (OrderingFilter, MatchFilter, DjangoFilterBackend, ProcessPermissionFilter)
    ordering_fields = ["creation_date", "key", "name", "owner"]
    ordering = ["creation_date", "key"]
    pagination_class = DefaultPageNumberPagination
    filterset_class = AlgoFilter

    def get_queryset(self):
        return Algo.objects.filter(channel=get_channel_name(self.request))


class AlgoViewSet(
    AlgoViewSetConfig, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet
):
    def create(self, request, *args, **kwargs):
        return create(request, self.basename, lambda data: self.get_success_headers(data))

    def update(self, request, *args, **kwargs):
        function = self.get_object()
        name = request.data.get("name")

        orc_algo = {
            "key": str(function.key),
            "name": name,
        }

        # send update to orchestrator
        # the modification in local db will be done upon corresponding event reception
        with get_orchestrator_client(get_channel_name(request)) as client:
            client.update_algo(orc_algo)

        return ApiResponse({}, status=status.HTTP_200_OK)


class CPAlgoViewSet(AlgoViewSetConfig, mixins.ListModelMixin, GenericViewSet):
    def get_queryset(self):
        compute_plan_key = self.kwargs.get("compute_plan_pk")
        validate_key(compute_plan_key)
        queryset = super().get_queryset()
        return queryset.filter(compute_tasks__compute_plan__key=compute_plan_key).distinct()


class AlgoPermissionViewSet(PermissionMixin, GenericViewSet):
    queryset = AlgoFiles.objects.all()
    serializer_class = AlgoFilesSerializer

    @action(detail=True)
    def file(self, request, *args, **kwargs):
        return self.download_file(request, Algo, "file", "algorithm_address")

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions
    @action(detail=True, url_path="description", url_name="description")
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, Algo, "description", "description_address")

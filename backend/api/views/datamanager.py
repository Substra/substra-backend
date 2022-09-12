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
from api.models import DataManager
from api.serializers import DataManagerSerializer
from api.serializers import DataManagerWithRelationsSerializer
from api.views.filters_utils import CharInFilter
from api.views.filters_utils import LogsPermissionFilter
from api.views.filters_utils import MatchFilter
from api.views.filters_utils import ProcessPermissionFilter
from api.views.utils import ApiResponse
from api.views.utils import PermissionMixin
from api.views.utils import ValidationExceptionError
from api.views.utils import get_channel_name
from libs.pagination import DefaultPageNumberPagination
from substrapp.models import DataManager as DataManagerFiles
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import DataManagerSerializer as DataManagerFilesSerializer
from substrapp.utils import get_hash

logger = structlog.get_logger(__name__)


def _register_in_orchestrator(request, instance):
    """Register datamanager in orchestrator."""

    current_site = settings.DEFAULT_DOMAIN
    permissions = request.data.get("permissions", {})
    logs_permission = request.data.get("logs_permission", {})

    orc_dm = {
        "key": str(instance.key),
        "name": request.data.get("name"),
        "opener": {
            "checksum": get_hash(instance.data_opener),
            "storage_address": current_site + reverse("api:data_manager-opener", args=[instance.key]),
        },
        "type": request.data.get("type"),
        "description": {
            "checksum": get_hash(instance.description),
            "storage_address": current_site + reverse("api:data_manager-description", args=[instance.key]),
        },
        "new_permissions": {
            "public": permissions.get("public"),
            "authorized_ids": permissions.get("authorized_ids"),
        },
        "metadata": request.data.get("metadata"),
        "logs_permission": {
            "public": logs_permission.get("public"),
            "authorized_ids": logs_permission.get("authorized_ids"),
        },
    }

    with get_orchestrator_client(get_channel_name(request)) as client:
        return client.register_datamanager(orc_dm)


def create(request, get_success_headers):
    """Create a new datamanager.

    The workflow is composed of several steps:
    - Save files in local database to get the addresses.
    - Register asset in the orchestrator.
    - Save metadata in local database.
    """
    # Step1: save files in local database
    data_opener = request.data.get("data_opener")
    try:
        checksum = get_hash(data_opener)
    except Exception as e:
        raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

    serializer = DataManagerFilesSerializer(
        data={
            "data_opener": data_opener,
            "description": request.data.get("description"),
            "name": request.data.get("name"),
            "checksum": checksum,
        }
    )

    try:
        serializer.is_valid(raise_exception=True)
    except Exception as e:
        raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

    instance = serializer.save()

    # Step2: register asset in orchestrator
    try:
        api_data = _register_in_orchestrator(request, instance)
    except Exception:
        instance.delete()  # warning: post delete signals are not executed by django rollback
        raise

    # Step3: save metadata in local database
    api_data["channel"] = get_channel_name(request)
    api_serializer = DataManagerSerializer(data=api_data)
    try:
        api_serializer.save_if_not_exists()
    except AlreadyExistsError:
        # May happen if the events app already processed the event pushed by the orchestrator
        data_manager = DataManager.objects.get(key=api_data["key"])
        data = DataManagerSerializer(data_manager).data
    except Exception:
        instance.delete()  # warning: post delete signals are not executed by django rollback
        raise
    else:
        data = api_serializer.data

    # Returns algo metadata from local database (and algo data) to ensure consistency between GET and CREATE views
    data.update(serializer.data)

    # Return ApiResponse
    headers = get_success_headers(data)
    return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)


class DataManagerFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter()
    compute_plan_key = CharInFilter(
        field_name="compute_tasks__compute_plan__key", distinct=True, label="compute_plan_key"
    )
    algo_key = CharFilter(field_name="compute_tasks__algo__key", distinct=True, label="algo_key")
    data_sample_key = CharInFilter(
        field_name="compute_tasks__data_samples__key", distinct=True, label="data_sample_key"
    )

    class Meta:
        model = DataManager
        fields = {
            "key": ["exact"],
            "name": ["exact"],
            "owner": ["exact"],
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


class DataManagerViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    filter_backends = (
        OrderingFilter,
        MatchFilter,
        DjangoFilterBackend,
        ProcessPermissionFilter,
        LogsPermissionFilter,
    )
    ordering_fields = ["creation_date", "key", "name", "owner"]
    ordering = ["creation_date", "key"]
    pagination_class = DefaultPageNumberPagination
    filterset_class = DataManagerFilter

    def get_queryset(self):
        return DataManager.objects.filter(channel=get_channel_name(self.request))

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DataManagerWithRelationsSerializer
        return DataManagerSerializer

    def create(self, request, *args, **kwargs):
        return create(request, lambda data: self.get_success_headers(data))

    def update(self, request, *args, **kwargs):
        datamanager = self.get_object()
        name = request.data.get("name")

        orc_algo = {
            "key": str(datamanager.key),
            "name": name,
        }

        # send update to orchestrator
        # the modification in local db will be done upon corresponding event reception
        with get_orchestrator_client(get_channel_name(request)) as client:
            client.update_datamanager(orc_algo)

        return ApiResponse({}, status=status.HTTP_200_OK)


class DataManagerPermissionViewSet(PermissionMixin, GenericViewSet):
    queryset = DataManagerFiles.objects.all()
    serializer_class = DataManagerFilesSerializer

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions

    @action(detail=True, url_path="description", url_name="description")
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, DataManager, "description", "description_address")

    @action(detail=True)
    def opener(self, request, *args, **kwargs):
        return self.download_file(request, DataManager, "data_opener", "opener_address")

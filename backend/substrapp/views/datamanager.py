import structlog
from django.urls import reverse
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.viewsets import GenericViewSet

from libs.pagination import DefaultPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import DataManager as DataManagerRep
from localrep.serializers import DataManagerSerializer as DataManagerRepSerializer
from localrep.serializers import DataManagerWithRelationsSerializer as DataManagerRepWithRelationsSerializer
from substrapp.models import DataManager
from substrapp.serializers import DataManagerSerializer
from substrapp.serializers import OrchestratorDataManagerSerializer
from substrapp.utils import get_hash
from substrapp.views.filters_utils import filter_queryset
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import PermissionMixin
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


def replace_storage_addresses(request, data_manager):
    data_manager["description"]["storage_address"] = request.build_absolute_uri(
        reverse("substrapp:data_manager-description", args=[data_manager["key"]])
    )
    data_manager["opener"]["storage_address"] = request.build_absolute_uri(
        reverse("substrapp:data_manager-opener", args=[data_manager["key"]])
    )


class DataManagerViewSet(mixins.CreateModelMixin, GenericViewSet):
    queryset = DataManager.objects.all()
    serializer_class = DataManagerSerializer
    pagination_class = DefaultPageNumberPagination

    def _register_in_orchestrator(self, request, instance):
        """Register datamanager in orchestrator."""
        orchestrator_serializer = OrchestratorDataManagerSerializer(
            data={
                "name": request.data.get("name"),
                "permissions": request.data.get("permissions"),
                "type": request.data.get("type"),
                "metadata": request.data.get("metadata"),
                "logs_permission": request.data.get("logs_permission"),
                "instance": instance,
            },
            context={"request": request},
        )
        orchestrator_serializer.is_valid(raise_exception=True)
        return orchestrator_serializer.create(get_channel_name(request), orchestrator_serializer.validated_data)

    def _create(self, request):
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

        serializer = DataManagerSerializer(
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
            localrep_data = self._register_in_orchestrator(request, instance)
        except Exception:
            instance.delete()  # warning: post delete signals are not executed by django rollback
            raise

        # Step3: save metadata in local database
        localrep_data["channel"] = get_channel_name(request)
        localrep_serializer = DataManagerRepSerializer(data=localrep_data)
        try:
            localrep_serializer.save_if_not_exists()
        except AlreadyExistsError:
            # May happen if the events app already processed the event pushed by the orchestrator
            data_manager = DataManagerRep.objects.get(key=localrep_data["key"])
            data = DataManagerRepSerializer(data_manager).data
        except Exception:
            instance.delete()  # warning: post delete signals are not executed by django rollback
            raise
        else:
            data = localrep_serializer.data

        # Returns algo metadata from local database (and algo data) to ensure consistency between GET and CREATE views
        data.update(serializer.data)
        return data

    def create(self, request, *args, **kwargs):
        data = self._create(request)
        headers = self.get_success_headers(data)
        return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)

    def _retrieve(self, request, key):
        validated_key = validate_key(key)
        try:
            data_manager = DataManagerRep.objects.filter(channel=get_channel_name(request)).get(key=validated_key)
        except DataManagerRep.DoesNotExist:
            raise NotFound
        data = DataManagerRepWithRelationsSerializer(data_manager).data

        replace_storage_addresses(request, data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        data = self._retrieve(request, key)
        return ApiResponse(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = DataManagerRep.objects.filter(channel=get_channel_name(request)).order_by("creation_date", "key")

        query_params = request.query_params.get("search")
        if query_params is not None:
            queryset = filter_queryset("dataset", queryset, query_params)
        queryset = self.paginate_queryset(queryset)

        data = DataManagerRepSerializer(queryset, many=True).data
        for data_manager in data:
            replace_storage_addresses(request, data_manager)

        return self.get_paginated_response(data)


class DataManagerPermissionViewSet(PermissionMixin, GenericViewSet):
    queryset = DataManager.objects.all()
    serializer_class = DataManagerSerializer

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions

    @action(detail=True, url_path="description", url_name="description")
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, DataManagerRep, "description", "description_address")

    @action(detail=True)
    def opener(self, request, *args, **kwargs):
        return self.download_file(request, DataManagerRep, "data_opener", "opener_address")

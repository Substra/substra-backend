import tempfile

import structlog
from django.http import Http404
from django.urls import reverse
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import GenericViewSet

from libs.pagination import DefaultPageNumberPagination
from libs.pagination import PaginationMixin
from substrapp.clients import node as node_client
from substrapp.models import DataManager
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import DataManagerSerializer
from substrapp.serializers import OrchestratorDataManagerSerializer
from substrapp.utils import get_hash
from substrapp.views.filters_utils import filter_list
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import PermissionMixin
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import node_has_process_permission
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


def replace_storage_addresses(request, data_manager):
    data_manager["description"]["storage_address"] = request.build_absolute_uri(
        reverse("substrapp:data_manager-description", args=[data_manager["key"]])
    )
    data_manager["opener"]["storage_address"] = request.build_absolute_uri(
        reverse("substrapp:data_manager-opener", args=[data_manager["key"]])
    )


class DataManagerViewSet(mixins.CreateModelMixin, PaginationMixin, GenericViewSet):
    queryset = DataManager.objects.all()
    serializer_class = DataManagerSerializer
    pagination_class = DefaultPageNumberPagination

    def commit(self, serializer, request):
        # create on db
        instance = serializer.save()

        # serialized data for orchestrator db
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
        if not orchestrator_serializer.is_valid():
            instance.delete()  # warning: post delete signals are not executed by django rollback
            raise ValidationError(orchestrator_serializer.errors)

        # create on orchestrator db
        try:
            data = orchestrator_serializer.create(get_channel_name(request), orchestrator_serializer.validated_data)
        except Exception:
            instance.delete()  # warning: post delete signals are not executed by django rollback
            raise

        merged_data = dict(serializer.data)
        merged_data.update(data)

        return merged_data

    def _create(self, request):
        data_opener = request.data.get("data_opener")
        try:
            checksum = get_hash(data_opener)
        except Exception as e:
            raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(
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
        else:
            return self.commit(serializer, request)

    def create(self, request, *args, **kwargs):
        data = self._create(request)
        headers = self.get_success_headers(data)
        return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)

    def create_or_update_datamanager(self, channel_name, datamanager, key):

        instance, created = DataManager.objects.update_or_create(key=key, name=datamanager["name"])

        if not instance.data_opener:
            content = node_client.get(
                channel=channel_name,
                node_id=datamanager["owner"],
                url=datamanager["opener"]["storage_address"],
                checksum=datamanager["opener"]["checksum"],
            )
            opener_file = tempfile.TemporaryFile()
            opener_file.write(content)
            instance.data_opener.save("opener.py", opener_file)

        if not instance.description:
            content = node_client.get(
                channel=channel_name,
                node_id=datamanager["owner"],
                url=datamanager["description"]["storage_address"],
                checksum=datamanager["description"]["checksum"],
            )
            description_file = tempfile.TemporaryFile()
            description_file.write(content)
            instance.description.save("description.md", description_file)

        return instance

    def _retrieve(self, request, key):
        validated_key = validate_key(key)

        with get_orchestrator_client(get_channel_name(request)) as client:
            # use query_dataset instead of query_datamanager to
            # get the datamanager but also its samples
            data = client.query_dataset(validated_key)

        # do not cache if node has not process permission
        if node_has_process_permission(data):
            try:
                instance = self.get_object()
            except Http404:
                instance = None
            finally:
                if not instance or not instance.description or not instance.data_opener:
                    instance = self.create_or_update_datamanager(get_channel_name(request), data, validated_key)

                # For security reason, do not give access to local file address
                # Restrain data to some fields
                serializer = self.get_serializer(instance, fields=("owner"))
                data.update(serializer.data)

        replace_storage_addresses(request, data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        data = self._retrieve(request, key)
        return ApiResponse(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        with get_orchestrator_client(get_channel_name(request)) as client:
            data = client.query_datamanagers()

        query_params = request.query_params.get("search")
        if query_params is not None:
            data = filter_list(object_type="dataset", data=data, query_params=query_params)

        for data_manager in data:
            replace_storage_addresses(request, data_manager)

        return self.paginate_response(data)


class DataManagerPermissionViewSet(PermissionMixin, GenericViewSet):
    queryset = DataManager.objects.all()
    serializer_class = DataManagerSerializer

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions

    @action(detail=True, url_path="description", url_name="description")
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, "query_datamanager", "description")

    @action(detail=True)
    def opener(self, request, *args, **kwargs):
        return self.download_file(request, "query_datamanager", "data_opener", "opener")

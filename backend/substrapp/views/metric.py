import tempfile

import structlog
from django.http import Http404
from django.urls import reverse
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from libs.pagination import DefaultPageNumberPagination
from libs.pagination import PaginationMixin
from substrapp.clients import node as node_client
from substrapp.models import Metric
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import MetricSerializer
from substrapp.serializers import OrchestratorMetricSerializer
from substrapp.utils import get_hash
from substrapp.views.filters_utils import filter_list
from substrapp.views.utils import PermissionMixin
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import node_has_process_permission
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


def replace_storage_addresses(request, metric):
    metric["description"]["storage_address"] = request.build_absolute_uri(
        reverse("substrapp:metric-description", args=[metric["key"]])
    )
    metric["address"]["storage_address"] = request.build_absolute_uri(
        reverse("substrapp:metric-metrics", args=[metric["key"]])
    )


class MetricViewSet(mixins.CreateModelMixin, PaginationMixin, GenericViewSet):
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer
    pagination_class = DefaultPageNumberPagination

    def commit(self, serializer, request):
        # create on db
        instance = serializer.save()

        # serialized data for orchestrator db
        orchestrator_serializer = OrchestratorMetricSerializer(
            data={
                "name": request.data.get("name"),
                "permissions": request.data.get("permissions"),
                "metadata": request.data.get("metadata"),
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
        description = request.data.get("description")
        try:
            checksum = get_hash(description)
        except Exception as e:
            raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(
            data={"address": request.data.get("file"), "description": description, "checksum": checksum}
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
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def create_or_update_metric_description(self, channel_name, metric, key):
        # We need to have, at least, metric description for the frontend
        content = node_client.get(
            channel_name=channel_name,
            node_id=metric["owner"],
            url=metric["description"]["storage_address"],
            content_checksum=metric["description"]["checksum"],
        )

        description_file = tempfile.TemporaryFile()
        description_file.write(content)

        instance, created = Metric.objects.update_or_create(key=key)
        instance.description.save("description.md", description_file)

        return instance

    def _retrieve(self, request, key):
        validated_key = validate_key(key)

        with get_orchestrator_client(get_channel_name(request)) as client:
            data = client.query_metric(validated_key)

        # verify if objective description exists for the frontend view
        # if not fetch it if it's possible
        # do not fetch objective description if node has no process permission
        if node_has_process_permission(data):
            try:
                instance = self.get_object()
            except Http404:
                instance = None
            finally:
                if not instance or not instance.description:
                    instance = self.create_or_update_metric_description(get_channel_name(request), data, validated_key)

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
        return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        with get_orchestrator_client(get_channel_name(request)) as client:
            data = client.query_metrics()

        query_params = request.query_params.get("search")
        if query_params is not None:
            data = filter_list(object_type="metric", data=data, query_params=query_params)

        for metric in data:
            replace_storage_addresses(request, metric)

        return self.paginate_response(data)


class MetricPermissionViewSet(PermissionMixin, GenericViewSet):
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions
    @action(detail=True, url_path="description", url_name="description")
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, "query_metric", "description")

    @action(detail=True)
    def metrics(self, request, *args, **kwargs):
        return self.download_file(request, "query_metric", "address")

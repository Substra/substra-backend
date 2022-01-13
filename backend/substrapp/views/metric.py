import tempfile

import structlog
from django.http import Http404
from django.urls import reverse
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.viewsets import GenericViewSet

from libs.pagination import DefaultPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import Metric as MetricRep
from localrep.serializers import MetricSerializer as MetricRepSerializer
from substrapp.clients import node as node_client
from substrapp.models import Metric
from substrapp.serializers import MetricSerializer
from substrapp.serializers import OrchestratorMetricSerializer
from substrapp.utils import get_hash
from substrapp.views.filters_utils import filter_queryset
from substrapp.views.utils import ApiResponse
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


class MetricViewSet(mixins.CreateModelMixin, GenericViewSet):
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer
    pagination_class = DefaultPageNumberPagination

    def _register_in_orchestrator(self, request, instance):
        """Register metric in orchestrator."""
        orchestrator_serializer = OrchestratorMetricSerializer(
            data={
                "name": request.data.get("name"),
                "permissions": request.data.get("permissions"),
                "metadata": request.data.get("metadata"),
                "instance": instance,
            },
            context={"request": request},
        )
        orchestrator_serializer.is_valid(raise_exception=True)
        return orchestrator_serializer.create(get_channel_name(request), orchestrator_serializer.validated_data)

    def _create(self, request):
        """Create a new metric.

        The workflow is composed of several steps:
        - Save metric data (description and Dockerfile archive) in local database.
          This is needed as we need the metric data addresses.
        - Register metric in the orchestrator.
        - Save metric metadata in local database.
        """
        # Step1: save metric data in local database
        description = request.data.get("description")
        try:
            checksum = get_hash(description)
        except Exception as e:
            raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

        serializer = MetricSerializer(
            data={"address": request.data.get("file"), "description": description, "checksum": checksum}
        )

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()

        # Step2: register metric in orchestrator
        try:
            localrep_data = self._register_in_orchestrator(request, instance)
        except Exception:
            instance.delete()  # warning: post delete signals are not executed by django rollback
            raise

        # Step3: save metric metadata in local database
        localrep_data["channel"] = get_channel_name(request)
        localrep_serializer = MetricRepSerializer(data=localrep_data)
        try:
            localrep_serializer.save_if_not_exists()
        except AlreadyExistsError:
            # May happen if the events app already processed the event pushed by the orchestrator
            metric = MetricRep.objects.get(key=localrep_data["key"])
            data = MetricRepSerializer(metric).data
        except Exception:
            instance.delete()  # warning: post delete signals are not executed by django rollback
            raise
        else:
            data = localrep_serializer.data

        # Returns metric metadata from local database to ensure consistency between GET and CREATE views
        data.update(serializer.data)
        return data

    def create(self, request, *args, **kwargs):
        data = self._create(request)
        headers = self.get_success_headers(data)
        return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)

    def create_or_update_metric_description(self, channel_name, metric, key):
        # We need to have, at least, metric description for the frontend
        content = node_client.get(
            channel=channel_name,
            node_id=metric["owner"],
            url=metric["description"]["storage_address"],
            checksum=metric["description"]["checksum"],
        )

        description_file = tempfile.TemporaryFile()
        description_file.write(content)

        instance, created = Metric.objects.update_or_create(key=key)
        instance.description.save("description.md", description_file)

        return instance

    def _retrieve(self, request, key):
        validated_key = validate_key(key)
        try:
            metric = MetricRep.objects.filter(channel=get_channel_name(request)).get(key=validated_key)
        except MetricRep.DoesNotExist:
            raise NotFound
        data = MetricRepSerializer(metric).data

        # verify if metric description exists for the frontend view
        # if not fetch it if it's possible
        # do not fetch metric description if node has no process permission
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
        return ApiResponse(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = MetricRep.objects.filter(channel=get_channel_name(request)).order_by("creation_date", "key")
        query_params = self.request.query_params.get("search")
        if query_params is not None:
            queryset = filter_queryset("metric", queryset, query_params)
        queryset = self.paginate_queryset(queryset)

        data = MetricRepSerializer(queryset, many=True).data

        for metric in data:
            replace_storage_addresses(request, metric)

        return self.get_paginated_response(data)


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

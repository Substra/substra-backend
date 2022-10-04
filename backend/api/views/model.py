import json

import structlog
from django.conf import settings
from django.db import models
from django.views.decorators import gzip
from django_filters.rest_framework import BaseInFilter
from django_filters.rest_framework import DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework import mixins
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

from api.errors import AlreadyExistsError
from api.errors import AssetPermissionError
from api.models import Model
from api.serializers import ModelSerializer
from api.views.utils import ApiResponse
from api.views.utils import IsCurrentBackendOrReadOnly
from api.views.utils import PermissionMixin
from api.views.utils import get_channel_name
from api.views.utils import if_true
from libs.pagination import DefaultPageNumberPagination
from organization.authentication import OrganizationUser
from substrapp.models import Model as ModelFiles
from substrapp.utils import get_owner

logger = structlog.get_logger(__name__)


def _create(request, basename, get_success_headers):
    """Create new models."""

    registered_models = json.loads(request.data["metadata"])

    data = []
    for registered_model in registered_models:
        registered_model["channel"] = get_channel_name(request)
        serializer = ModelSerializer(data=registered_model)
        try:
            serializer.save_if_not_exists()
        except AlreadyExistsError:
            # May happen if the events app already processed the event pushed by the orchestrator
            model = Model.objects.get(key=registered_model["key"])
            serializer = ModelSerializer(model)

        data.append(serializer.data)

    # Return ApiResponse
    headers = get_success_headers(data)
    return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)


class ModelFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter()
    compute_task_key = BaseInFilter(field_name="compute_task__key")

    class Meta:
        model = Model
        fields = {
            "owner": ["exact"],
            "key": ["exact"],
            "compute_task": ["exact"],
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


class ModelViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    filter_backends = (OrderingFilter, DjangoFilterBackend)
    pagination_class = DefaultPageNumberPagination
    serializer_class = ModelSerializer
    ordering_fields = ["creation_date", "key"]
    ordering = ["creation_date", "key"]
    filterset_class = ModelFilter

    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES + [BasicAuthentication]
    permission_classes = [IsAuthenticated, IsCurrentBackendOrReadOnly]

    def get_queryset(self):
        return Model.objects.filter(channel=get_channel_name(self.request))

    def create(self, request, *args, **kwargs):
        return _create(request, self.basename, lambda data: self.get_success_headers(data))


class ModelPermissionViewSet(PermissionMixin, GenericViewSet):

    queryset = ModelFiles.objects.all()

    def check_access(self, channel_name: str, user, asset, is_proxied_request: bool) -> None:
        """Return true if API consumer is allowed to access the model.

        Args:
            is_proxied_request: True if the API consumer is another backend-server proxying a user request

        Raises:
            AssetPermissionError
        """
        if user.is_anonymous:
            raise AssetPermissionError()

        elif type(user) is OrganizationUser and is_proxied_request:  # Export request (proxied)
            self._check_export_enabled(channel_name)
            field, organization_id = "download", user.username

        elif type(user) is OrganizationUser:  # Organization-to-organization download
            field, organization_id = "process", user.username

        else:  # user is an end-user (not a OrganizationUser): this is an export request
            self._check_export_enabled(channel_name)
            field, organization_id = "download", get_owner()

        if not asset.is_public(field) and organization_id not in asset.get_authorized_ids(field):
            raise AssetPermissionError()

    @staticmethod
    def _check_export_enabled(channel_name):
        channel = settings.LEDGER_CHANNELS[channel_name]
        if not channel.get("model_export_enabled", False):
            raise AssetPermissionError(f"Disabled: model_export_enabled is disabled on {settings.LEDGER_MSP_ID}")

    @if_true(gzip.gzip_page, settings.GZIP_MODELS)
    @action(detail=True)
    def file(self, request, *args, **kwargs):
        return self.download_file(request, Model, "file", "model_address")

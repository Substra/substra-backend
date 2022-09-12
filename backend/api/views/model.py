import structlog
from django.conf import settings
from django.db import models
from django.views.decorators import gzip
from django_filters.rest_framework import BaseInFilter
from django_filters.rest_framework import DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

from api.models import Model as ModelRep
from api.serializers import ModelSerializer as ModelRepSerializer
from api.views.filters_utils import ChoiceInFilter
from api.views.utils import AssetPermissionError
from api.views.utils import PermissionMixin
from api.views.utils import get_channel_name
from api.views.utils import if_true
from libs.pagination import DefaultPageNumberPagination
from organization.authentication import OrganizationUser
from substrapp import exceptions
from substrapp.models import Model
from substrapp.utils import get_owner

logger = structlog.get_logger(__name__)


def validate_category(key, values):
    if key == "category":
        try:
            for value in values:
                getattr(ModelRep.Category, value)
        except AttributeError as e:
            raise exceptions.BadRequestError(f"Wrong {key} value: {e}")
    return key, values


class ModelRepFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter()
    category = ChoiceInFilter(
        field_name="category",
        choices=ModelRep.Category.choices,
    )
    compute_task_key = BaseInFilter(field_name="compute_task__key")

    class Meta:
        model = ModelRep
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


class ModelViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    filter_backends = (OrderingFilter, DjangoFilterBackend)
    pagination_class = DefaultPageNumberPagination
    serializer_class = ModelRepSerializer
    ordering_fields = ["creation_date", "key"]
    ordering = ["creation_date", "key"]
    filterset_class = ModelRepFilter

    def get_queryset(self):
        return ModelRep.objects.filter(channel=get_channel_name(self.request))


class ModelPermissionViewSet(PermissionMixin, GenericViewSet):

    queryset = Model.objects.all()

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
        return self.download_file(request, ModelRep, "file", "model_address")

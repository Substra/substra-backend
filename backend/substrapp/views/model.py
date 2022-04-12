import structlog
from django.conf import settings
from django.views.decorators import gzip
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

import orchestrator.model_pb2 as model_pb2
from libs.pagination import DefaultPageNumberPagination
from localrep.models import Model as ModelRep
from localrep.serializers import ModelSerializer as ModelRepSerializer
from node.authentication import NodeUser
from substrapp import exceptions
from substrapp.models import Model
from substrapp.utils import get_owner
from substrapp.views.filters_utils import CustomSearchFilter
from substrapp.views.utils import AssetPermissionError
from substrapp.views.utils import PermissionMixin
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import if_true

logger = structlog.get_logger(__name__)


def map_category(key, values):
    if key == "category":
        try:
            values = [model_pb2.ModelCategory.Value(value) for value in values]
        except ValueError as e:
            raise exceptions.BadRequestError(f"Wrong {key} value: {e}")
    return key, values


class ModelViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    filter_backends = (OrderingFilter, CustomSearchFilter)
    pagination_class = DefaultPageNumberPagination
    serializer_class = ModelRepSerializer
    ordering_fields = ["creation_date", "key"]
    ordering = ["creation_date", "key"]
    custom_search_object_type = "model"
    custom_search_mapping_callback = map_category

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

        elif type(user) is NodeUser and is_proxied_request:  # Export request (proxied)
            self._check_export_enabled(channel_name)
            field, node_id = "download", user.username

        elif type(user) is NodeUser:  # Node-to-node download
            field, node_id = "process", user.username

        else:  # user is an end-user (not a NodeUser): this is an export request
            self._check_export_enabled(channel_name)
            field, node_id = "download", get_owner()

        if not asset.is_public(field) and node_id not in asset.get_authorized_ids(field):
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

import tempfile
import structlog
from functools import wraps
from django.conf import settings
from django.middleware.gzip import GZipMiddleware
from django.urls.base import reverse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp import exceptions
from node.authentication import NodeUser
from substrapp.models import Model
from substrapp.views.utils import (validate_key, get_remote_asset, PermissionMixin, get_channel_name,
                                   AssetPermissionError)
from substrapp.views.filters_utils import filter_list
from libs.pagination import DefaultPageNumberPagination, PaginationMixin

from substrapp.orchestrator import get_orchestrator_client
from orchestrator.error import OrcError

logger = structlog.get_logger(__name__)


def replace_storage_addresses(request, model):
    # Here we might need to check if there is a storage address, might not be the case with
    # delete_intermediary_model
    if 'address' in model and model['address']:
        model['address']['storage_address'] = request.build_absolute_uri(
            reverse('substrapp:model-file', args=[model['key']])
        )


class ModelViewSet(PaginationMixin,
                   GenericViewSet):
    queryset = Model.objects.all()
    pagination_class = DefaultPageNumberPagination

    def create_or_update_model(self, channel_name, traintuple, key):
        if traintuple["out_model"] is None:
            raise Exception(
                f"This traintuple related to this model key {key} does not have a out_model"
            )

        # get model from remote node
        url = traintuple["out_model"]["storage_address"]

        content = get_remote_asset(
            channel_name, url, traintuple["creator"], traintuple["key"]
        )

        # write model in local db for later use
        tmp_model = tempfile.TemporaryFile()
        tmp_model.write(content)
        instance, created = Model.objects.update_or_create(key=key, validated=True)
        instance.file.save("model", tmp_model)

        return instance

    def _retrieve(self, request, key):
        validated_key = validate_key(key)

        with get_orchestrator_client(get_channel_name(request)) as client:
            data = client.query_model(validated_key)

        replace_storage_addresses(request, data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(request, key)
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except exceptions.BadRequestError:
            raise
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                data = client.query_models()
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        query_params = request.query_params.get('search')
        if query_params is not None:
            try:
                data = filter_list(
                    object_type="model",
                    data=data,
                    query_params=query_params,
                )
            except OrcError as rpc_error:
                return Response({'message': rpc_error.details}, status=rpc_error.http_status())
            except Exception as e:
                logger.exception(e)
                return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        for model in data:
            replace_storage_addresses(request, model)

        return self.paginate_response(data)


def gzip_action(func):
    gz = GZipMiddleware()

    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        resp = func(self, request, *args, **kwargs)
        return gz.process_response(request, resp)

    if getattr(settings, "GZIP_MODELS"):
        return wrapper
    return func


class ModelPermissionViewSet(PermissionMixin, GenericViewSet):

    queryset = Model.objects.all()

    def check_access(
        self, channel_name: str, user, asset, is_proxied_request: bool
    ) -> None:
        """Return true if API consumer is allowed to access the model.

        :param is_proxied_request: True if the API consumer is another backend-server proxying a user request
        :raises: AssetPermissionError
        """
        if user.is_anonymous:
            raise AssetPermissionError()

        elif type(user) is NodeUser and is_proxied_request:  # Export request (proxied)
            self._check_export_enabled(channel_name)
            self._check_permission("download", asset, node_id=user.username)

        elif type(user) is NodeUser:  # Node-to-node download
            self._check_permission("process", asset, node_id=user.username)

        else:  # user is an end-user (not a NodeUser): this is an export request
            self._check_export_enabled(channel_name)
            self._check_permission("download", asset, node_id=settings.LEDGER_MSP_ID)

    def get_storage_address(self, asset, ledger_field) -> str:
        return asset["address"]["storage_address"]

    @staticmethod
    def _check_export_enabled(channel_name):
        channel = settings.LEDGER_CHANNELS[channel_name]
        if not channel.get("model_export_enabled", False):
            raise AssetPermissionError(
                f"Disabled: model_export_enabled is disabled on {settings.LEDGER_MSP_ID}"
            )

    @staticmethod
    def _check_permission(permission_type, asset, node_id):
        permissions = asset["permissions"][permission_type]
        if not permissions["public"] and node_id not in permissions["authorized_ids"]:
            raise AssetPermissionError(
                f'{node_id} doesn\'t have permission to download model {asset["key"]}'
            )

    @gzip_action
    @action(detail=True)
    def file(self, request, *args, **kwargs):
        return self.download_file(
            request, query_method="query_model", django_field="file"
        )

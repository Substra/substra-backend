import os
import uuid
from typing import Callable
from wsgiref.util import is_hop_by_hop

import django.http
from django.conf import settings
from django.forms import CharField
from django.forms import ChoiceField
from django.forms import UUIDField
from django_filters.rest_framework import BaseInFilter
from django_filters.rest_framework import CharFilter
from django_filters.rest_framework import ChoiceFilter
from django_filters.rest_framework import UUIDFilter
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings

from localrep.models import ComputeTask as ComputeTaskRep
from node.authentication import NodeUser
from substrapp.clients import node as node_client
from substrapp.exceptions import AssetPermissionError
from substrapp.exceptions import BadRequestError
from substrapp.storages.minio import MinioStorage
from substrapp.utils import get_owner

CP_BASENAME_PREFIX = "compute_plan_"

TASK_CATEGORY = {
    "traintuple": ComputeTaskRep.Category.TASK_TRAIN,
    "testtuple": ComputeTaskRep.Category.TASK_TEST,
    "aggregatetuple": ComputeTaskRep.Category.TASK_AGGREGATE,
    "composite_traintuple": ComputeTaskRep.Category.TASK_COMPOSITE,
}

HTTP_HEADER_PROXY_ASSET = "Substra-Proxy-Asset"


class ApiResponse(Response):
    """The Content-Disposition header is used for downloads and web service responses
    and indicates to the browser whether the provided file is to be displayed (inline)
    or stored (attachment).
    Some browsers display the file content in the browser if no Content-Disposition header
    is set. Using Content-Disposition: attachment; filename="API-response.json" in production
    is important because it signals the browser not to display the response in the browser.
    """

    def __init__(self, data=None, status=None, template_name=None, headers=None, exception=False, content_type=None):

        if headers is not None:
            if "Content-Disposition" not in headers:
                headers = {**headers, **settings.CONTENT_DISPOSITION_HEADER}
        else:
            headers = settings.CONTENT_DISPOSITION_HEADER

        super().__init__(data, status, template_name, headers, exception, content_type)

    @staticmethod
    def add_content_disposition_header(response):
        response.headers = {**response.headers, **settings.CONTENT_DISPOSITION_HEADER}
        return response


class CustomFileResponse(django.http.FileResponse):
    def set_headers(self, filelike):
        super().set_headers(filelike)

        self["Access-Control-Expose-Headers"] = "Content-Disposition"


class PermissionMixin(object):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES + [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def check_access(self, channel_name: str, user, asset, is_proxied_request: bool) -> None:
        """Returns true if API consumer is allowed to access data.

        :param is_proxied_request: True if the API consumer is another backend-server proxying a user request
        :raises: AssetPermissionError
        """
        if user.is_anonymous:  # safeguard, should never happen
            raise AssetPermissionError()

        if type(user) is NodeUser:  # for node
            node_id = user.username
        else:
            # for classic user, test on current msp id
            node_id = get_owner()

        if not asset.is_public("process") and node_id not in asset.get_authorized_ids("process"):
            raise AssetPermissionError()

    def download_file(self, request, asset_class, content_field, address_field):
        if settings.ISOLATED:
            return ApiResponse({"message": "Asset not available in isolated mode"}, status=status.HTTP_410_GONE)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        channel_name = get_channel_name(request)

        validated_key = validate_key(key)
        asset = asset_class.objects.filter(channel=channel_name).get(key=validated_key)

        try:
            self.check_access(channel_name, request.user, asset, is_proxied_request(request))
        except AssetPermissionError as e:
            return ApiResponse({"message": str(e)}, status=status.HTTP_403_FORBIDDEN)

        url = getattr(asset, address_field)
        if not url:
            return ApiResponse({"message": "Asset not available anymore"}, status=status.HTTP_410_GONE)

        if get_owner() == asset.get_owner():
            response = self._get_local_file_response(content_field)
        else:
            response = self._download_remote_file(channel_name, asset.get_owner(), url)

        return response

    def _get_local_file_response(self, content_field):
        obj = self.get_object()
        data = getattr(obj, content_field)

        if isinstance(data.storage, MinioStorage):
            filename = str(obj.key)
        else:
            filename = os.path.basename(data.path)
            data = open(data.path, "rb")

        response = CustomFileResponse(
            data,
            as_attachment=True,
            filename=filename,
        )
        return response

    def _download_remote_file(self, channel_name: str, owner: str, url: str) -> django.http.FileResponse:
        proxy_response = node_client.http_get(
            channel=channel_name,
            node_id=owner,
            url=url,
            stream=True,
            headers={HTTP_HEADER_PROXY_ASSET: "True"},
        )
        response = CustomFileResponse(
            streaming_content=(chunk for chunk in proxy_response.iter_content(512 * 1024)),
            status=proxy_response.status_code,
        )

        for header in proxy_response.headers:
            # We don't use hop_by_hop headers since they are incompatible
            # with WSGI
            if not is_hop_by_hop(header):
                response[header] = proxy_response.headers.get(header)

        return response


def validate_key(key) -> str:
    """Validates an asset key and return the validated key.

    Args:
        key (str): A valid UUID in string format

    Raises:
        BadRequestError: Raised if the key value isn't an UUID.

    Returns:
        str: A valid UUID in str standard format
    """
    try:
        uid = to_string_uuid(key)
    except ValueError:
        raise BadRequestError(f'key is not a valid UUID: "{key}"')
    return uid


def validate_sort(sort):
    if sort not in ["asc", "desc"]:
        raise BadRequestError(f"Invalid sort value (must be either 'desc' or 'asc'): {sort}")


class ValidationExceptionError(Exception):
    def __init__(self, data, key, st):
        self.data = data
        self.key = key
        self.st = st
        super(ValidationExceptionError).__init__()


def get_channel_name(request):

    if hasattr(request.user, "channel"):
        return request.user.channel.name

    if "Substra-Channel-Name" in request.headers:
        return request.headers["Substra-Channel-Name"]

    raise BadRequestError("Could not determine channel name")


def is_proxied_request(request) -> bool:
    """Return True if the API consumer is another backend-server node proxying a user request.

    :param request: incoming HTTP request
    """
    return HTTP_HEADER_PROXY_ASSET in request.headers


def to_string_uuid(str_or_hex_uuid: uuid.UUID) -> str:
    """converts an UUID string of form 32 char hex string or standard form to a standard form UUID.

    Args:
        str_or_hex_uuid (str): input UUID of form '412511b1-f9f5-49cc-a4bb-4f1640c877f6'
            or '412511b1f9f549cca4bb4f1640c877f6'.

    Returns:
        str: UUID of form '412511b1-f9f5-49cc-a4bb-4f1640c877f6'
    """
    return str(uuid.UUID(str_or_hex_uuid))


def if_true(decorator: Callable, condition: bool):
    """Decorates a function only if the condition is true

    Args:
        decorator (Callable): The decorator function to apply
        condition (bool): If true the decorator is applied, else we just run the decorated function
    """

    def wrapper(func):
        if not condition:
            return func
        return decorator(func)

    return wrapper


def permissions_intersect(x, y):
    if x["public"] and y["public"]:
        return {"public": True}

    elif x["public"] and not y["public"]:
        return {"public": False, "authorized_ids": y["authorized_ids"]}

    elif not x["public"] and y["public"]:
        return {"public": False, "authorized_ids": x["authorized_ids"]}

    else:
        return {
            "public": False,
            "authorized_ids": list(set(x["authorized_ids"]).intersection(set(y["authorized_ids"]))),
        }


def permissions_union(x, y):
    if x["public"] or y["public"]:
        return {"public": True}
    return {
        "public": False,
        "authorized_ids": list(set(x["authorized_ids"]).union(set(y["authorized_ids"]))),
    }


class MatchFilter(SearchFilter):
    """Full text search in a selected number of fields.

    Searches by default in key and name.
    The list can be customized through the search_fields attribute on the view."""

    search_param = "match"
    default_search_fields = ("key", "name")

    def get_search_fields(self, view, request):
        return getattr(view, "search_fields", self.default_search_fields)


class ChoiceInFilter(BaseInFilter, ChoiceFilter):
    """Allow choice field to be filtered with IN lookup passing comma separated values list"""

    field_class = ChoiceField


class CharInFilter(BaseInFilter, CharFilter):
    """Allow char field to be filtered with IN lookup passing comma separated values list"""

    field_class = CharField


class UUIDInFilter(BaseInFilter, UUIDFilter):
    """Allow uuid field to be filtered with IN lookup passing comma separated values list"""

    field_class = UUIDField

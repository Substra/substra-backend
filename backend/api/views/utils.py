import os
import uuid
from typing import Callable
from typing import Type
from typing import TypeVar
from wsgiref.util import is_hop_by_hop

import django.http
from django.conf import settings
from django.db import models
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import SAFE_METHODS
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import ViewSet

from api.errors import AssetPermissionError
from api.errors import BadRequestError
from libs.permissions import IsAuthorized
from organization.authentication import OrganizationUser
from substrapp.clients import organization as organization_client
from substrapp.storages.minio import MinioStorage
from substrapp.utils import get_owner

CP_BASENAME_PREFIX = "compute_plan_"

HTTP_HEADER_PROXY_ASSET = "Substra-Proxy-Asset"

AssetType = TypeVar("AssetType", bound=models.Model)
LocalFileType = TypeVar("LocalFileType", bound=models.Model)


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
    permission_classes = [IsAuthorized]

    def check_access(self, channel_name: str, user, asset, is_proxied_request: bool) -> None:
        """Returns true if API consumer is allowed to access data.

        :param is_proxied_request: True if the API consumer is another backend-server proxying a user request
        :raises: AssetPermissionError
        """
        if user.is_anonymous:  # safeguard, should never happen
            raise AssetPermissionError()

        if type(user) is OrganizationUser:  # for organization
            organization_id = user.username
        else:
            # for classic user, test on current msp id
            organization_id = get_owner()

        if not asset.is_public("process") and organization_id not in asset.get_authorized_ids("process"):
            raise AssetPermissionError()

    def get_key(self, request) -> str:
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        return validate_key(key)

    def get_asset(self, request, key: str, channel_name: str, asset_class: Type[AssetType]) -> AssetType:
        asset = asset_class.objects.filter(channel=channel_name).get(key=key)
        self.check_access(channel_name, request.user, asset, is_proxied_request(request))

        return asset

    def download_file(
        self,
        request,
        *,
        asset_class: Type[AssetType],
        local_file_class: Type[LocalFileType],
        content_field: str,
        address_field: str,
    ):
        if settings.ISOLATED:
            return ApiResponse({"detail": "Asset not available in isolated mode"}, status=status.HTTP_410_GONE)

        key = self.get_key(request)
        channel_name = get_channel_name(request)
        try:
            asset = self.get_asset(request, key, channel_name, asset_class)
        except AssetPermissionError as e:
            return ApiResponse({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        print("ok we got the asset")
        url = getattr(asset, address_field)
        print("ok we got the url")
        if not url:
            return ApiResponse({"detail": "Asset not available anymore"}, status=status.HTTP_410_GONE)

        return get_file_response(
            key=key,
            local_file_class=local_file_class,
            owner=asset.get_owner(),
            content_field=content_field,
            channel_name=channel_name,
            url=url,
        )


def get_file_response(
    *, local_file_class: Type[LocalFileType], content_field: str, key: str, owner: str, channel_name: str, url: str
) -> django.http.FileResponse:
    if get_owner() == owner:
        local_file = local_file_class.objects.get(pk=key)
        response = _get_local_file_response(local_file, key, content_field)
    else:
        response = _download_remote_file(channel_name, owner, url)

    return response


def _get_local_file_response(local_file: LocalFileType, key: str, content_field: str):
    data = getattr(local_file, content_field)

    if isinstance(data.storage, MinioStorage):
        filename = key
    else:
        filename = os.path.basename(data.path)
        data = open(data.path, "rb")

    response = CustomFileResponse(
        data,
        as_attachment=True,
        filename=filename,
    )
    return response


def _download_remote_file(channel_name: str, owner: str, url: str) -> django.http.FileResponse:
    proxy_response = organization_client.streamed_get(
        channel=channel_name,
        organization_id=owner,
        url=url,
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


def validate_metadata(metadata: dict) -> dict:
    """Validates an asset metadata keys and return the validated metadata dict.

    Args:
        metadata (dict): A metadata dict

    Raises:
        BadRequestError: Raised if `__` is present in one of the metadata keys.

    Returns:
        dict: A valid dict of metadata
    """

    if metadata and any("__" in key for key in metadata):
        raise BadRequestError('"__" cannot be used in a metadata key, please use simple underscore instead')
    else:
        return metadata


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
        return request.user.channel.channel_name

    # in case of node-to-node authentication, channel name is defined in header
    if "Substra-Channel-Name" in request.headers:
        return request.headers["Substra-Channel-Name"]

    raise BadRequestError("Could not determine channel name")


def is_proxied_request(request) -> bool:
    """Return True if the API consumer is another backend-server organization proxying a user request.

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


class IsCurrentBackendOrReadOnly(BasePermission):
    def has_permission(self, request: Request, view: ViewSet) -> bool:
        if request.method in SAFE_METHODS:
            return True
        elif (
            request.method in ["POST", "PUT"]
            and type(request.user) is OrganizationUser
            and request.user.username == get_owner()
        ):
            return True
        else:
            return False

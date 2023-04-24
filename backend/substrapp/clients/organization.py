"""Client to get asset from another organization server.

This module provides various helpers to access assets stored in remote Organizations.
It verifies as well the integrity of downloaded asset when possible.
"""
import enum
import hashlib
import os
import typing

import requests
import structlog
from django.conf import settings
from requests.auth import HTTPBasicAuth

from substrapp.exceptions import IntegrityError
from substrapp.exceptions import OrganizationError
from substrapp.exceptions import OrganizationHttpError
from substrapp.utils import compute_hash

logger = structlog.get_logger(__name__)


class _Method(enum.Enum):
    POST = enum.auto()
    GET = enum.auto()
    PUT = enum.auto()


_LEDGER_MSP_ID: str = settings.LEDGER_MSP_ID
_HTTP_VERIFY: bool = not settings.DEBUG
_HTTP_TIMEOUT: int = settings.HTTP_CLIENT_TIMEOUT_SECONDS
_HTTP_STREAM_CHUNK_SIZE: int = 1024 * 1024  # in bytes, equivalent to 1 megabyte
_HTTP_METHOD_TO_FUNC: dict[_Method, typing.Callable[..., requests.Response]] = {
    _Method.GET: requests.get,
    _Method.POST: requests.post,
    _Method.PUT: requests.put,
}


def _fetch_secret(organization_id: str) -> str:
    """Find credentials to authenticate with remote organization.

    Args:
        organization_id (str): MSPID of the organization we want to communicate with.

    Returns:
        str: password used to communicate with that organization.
    """
    from organization.models import OutgoingOrganization

    try:
        outgoing = OutgoingOrganization.objects.get(organization_id=organization_id)
    except OutgoingOrganization.DoesNotExist:
        logger.error("Missing outgoing credentials", organization_id=organization_id)
        raise
    return outgoing.secret


def _add_mandatory_headers(headers: dict[str, str], channel: str) -> dict[str, str]:
    """Adds the required headers for org to org communication to the headers dict.

    Args:
        headers (dict[str, str]): user provided headers
        channel (str): channel name

    Returns:
        dict[str, str]: updated headers with the Accept and Channel header set
    """
    complete_headers = {}
    complete_headers.update(headers)
    complete_headers.update(
        {
            "Accept": "application/json;version=0.0",
            "Substra-Channel-Name": channel,
        }
    )
    return complete_headers


def _http_request_kwargs(data: typing.Optional[dict], stream: bool) -> dict:
    """builds a dict with extra request arguments

    Args:
        data (typing.Optional[dict]): potential data that can be set if the request is a POST
        stream (bool): whether the response should be streamed or not

    Returns:
        dict: a dict of requests keyword arguments
    """
    kwargs = {}
    if stream:
        kwargs["stream"] = True
    if data is not None:
        kwargs["data"] = data
    return kwargs


def _http_request(
    method: _Method,
    channel: str,
    organization_id: str,
    url: str,
    headers: typing.Optional[dict[str, str]] = None,
    data: typing.Optional[dict] = None,
    stream: bool = False,
) -> requests.Response:
    """A low level http request builder

    Args:
        method (_Method): http method
        channel (str): substra channel name
        organization_id (str): name of the organization we are trying to query
        url (str): url to which we should make the request
        headers (typing.Optional[dict[str, str]], optional): user provided headers. Defaults to None.
        data (typing.Optional[dict], optional): user provided data for the request. Defaults to None.
        stream (bool, optional): whether the response should be streamed or not. Defaults to False.

    Returns:
        requests.Response: a requests response object with a successful http response code
    """
    headers = headers or {}
    secret = _fetch_secret(organization_id)

    response = None
    try:
        response = _HTTP_METHOD_TO_FUNC[method](
            url,
            headers=_add_mandatory_headers(headers, channel),
            auth=HTTPBasicAuth(_LEDGER_MSP_ID, secret),
            verify=_HTTP_VERIFY,
            timeout=_HTTP_TIMEOUT,
            **_http_request_kwargs(data, stream),
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise OrganizationError(f"Failed to connect to {organization_id}") from exc

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else None
        raise OrganizationHttpError(url=url, status_code=status_code)

    return response


def download(
    channel: str,
    organization_id: str,
    url: str,
    destination: str,
    checksum: str,
    salt: typing.Optional[str] = None,
) -> None:
    """Download an asset data to a file (not atomic)."""
    response = _http_request(_Method.GET, channel, organization_id, url, stream=True)
    try:
        downloaded_file_checksum = hashlib.sha256()
        with open(destination, "wb") as fp:
            for chunk in response.iter_content(_HTTP_STREAM_CHUNK_SIZE):
                fp.write(chunk)
                downloaded_file_checksum.update(chunk)
    finally:
        response.close()

    if salt is not None:
        encoded_salt = salt.encode()
        downloaded_file_checksum.update(encoded_salt)

    if downloaded_file_checksum.hexdigest() != checksum:
        os.remove(destination)
        raise IntegrityError(
            f"url {url}: checksum doesn't match expected={checksum} vs actual={downloaded_file_checksum}"
        )


def get(
    channel: str,
    organization_id: str,
    url: str,
    checksum: str,
    salt: typing.Optional[str] = None,
) -> bytes:
    """Get asset data."""
    content = _http_request(_Method.GET, channel, organization_id, url).content
    new_checksum = compute_hash(content, key=salt)
    if new_checksum != checksum:
        raise IntegrityError(f"url {url}: checksum doesn't match {checksum} vs {new_checksum}")
    return content


def post(
    channel: str,
    organization_id: str,
    url: str,
    data: dict,
) -> bytes:
    """Post asset data."""
    return _http_request(_Method.POST, channel, organization_id, url, data=data).content


def put(
    channel: str,
    organization_id: str,
    url: str,
    data: dict,
) -> bytes:
    """Update asset data."""
    return _http_request(_Method.PUT, channel, organization_id, url, data=data).content


def streamed_get(channel: str, organization_id: str, url: str, headers: dict[str, str]) -> requests.Response:
    """Query another backend and return a streamed response object"""
    return _http_request(_Method.GET, channel, organization_id, url, stream=True, headers=headers)

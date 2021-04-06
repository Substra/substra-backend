import os
import uuid

from django.http import FileResponse
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings

from node.authentication import NodeUser
from substrapp.ledger.api import get_object_from_ledger
from substrapp.ledger.exceptions import LedgerError
from substrapp.utils import NodeError, get_remote_file, get_owner, get_remote_file_content
from node.models import OutgoingNode

from django.conf import settings
from rest_framework import status
from requests.auth import HTTPBasicAuth
from wsgiref.util import is_hop_by_hop

from substrapp import exceptions

HTTP_HEADER_PROXY_ASSET = 'Substra-Proxy-Asset'


class PermissionError(Exception):
    def __init__(self, message='Unauthorized'):
        Exception.__init__(self, message)


def authenticate_outgoing_request(outgoing_node_id):
    try:
        outgoing = OutgoingNode.objects.get(node_id=outgoing_node_id)
    except OutgoingNode.DoesNotExist:
        raise NodeError(f'Unauthorized to call remote node with node_id: {outgoing_node_id}')

    # to authenticate to remote node we use the current node id
    # with the associated outgoing secret.
    current_node_id = get_owner()

    return HTTPBasicAuth(current_node_id, outgoing.secret)


def get_remote_asset(channel_name, url, node_id, content_checksum, salt=None):
    auth = authenticate_outgoing_request(node_id)
    return get_remote_file_content(channel_name, url, auth, content_checksum, salt=salt)


class CustomFileResponse(FileResponse):
    def set_headers(self, filelike):
        super(CustomFileResponse, self).set_headers(filelike)

        self['Access-Control-Expose-Headers'] = 'Content-Disposition'


def node_has_process_permission(asset):
    """Check if current node can process input asset."""
    permission = asset['permissions']['process']
    return permission['public'] or get_owner() in permission['authorized_ids']


class PermissionMixin(object):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES + [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def check_access(self, channel_name: str, user, asset, is_proxied_request: bool) -> None:
        """Returns true if API consumer is allowed to access data.

        :param is_proxied_request: True if the API consumer is another backend-server proxying a user request
        :raises: PermissionError
        """
        if user.is_anonymous:  # safeguard, should never happened
            raise PermissionError()

        if type(user) is NodeUser:  # for node
            permission = asset['permissions']['process']
            node_id = user.username
        else:
            # for classic user, test on current msp id
            # TODO: This should be 'download' instead of 'process',
            #       but 'download' is not consistently exposed by chaincode yet.
            permission = asset['permissions']['process']
            node_id = get_owner()

        if not permission['public'] and node_id not in permission['authorized_ids']:
            raise PermissionError()

    def get_storage_address(self, asset, ledger_field) -> str:
        return asset[ledger_field]['storage_address']

    def download_file(self, request, django_field, ledger_field=None):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        channel_name = get_channel_name(request)

        try:
            asset = get_object_from_ledger(channel_name, key, self.ledger_query_call)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        try:
            self.check_access(channel_name, request.user, asset, is_proxied_request(request))
        except PermissionError as e:
            return Response({'message': str(e)},
                            status=status.HTTP_403_FORBIDDEN)

        if get_owner() == asset['owner']:
            response = self._download_local_file(django_field)
        else:
            if not ledger_field:
                ledger_field = django_field
            storage_address = self.get_storage_address(asset, ledger_field)
            response = self._download_remote_file(channel_name, storage_address, asset)

        return response

    def download_local_file(self, request, django_field):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        channel_name = get_channel_name(request)

        try:
            asset = get_object_from_ledger(channel_name, key, self.ledger_query_call)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        try:
            self.check_access(channel_name, request.user, asset, is_proxied_request(request))
        except PermissionError as e:
            return Response({'message': str(e)},
                            status=status.HTTP_403_FORBIDDEN)

        return self._download_local_file(django_field)

    def _download_local_file(self, django_field):
        obj = self.get_object()
        data = getattr(obj, django_field)
        response = CustomFileResponse(
            open(data.path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(data.path)
        )
        return response

    def _download_remote_file(self, channel_name, storage_address, asset):
        node_id = asset['owner']
        auth = authenticate_outgoing_request(node_id)

        r = get_remote_file(
            channel_name,
            storage_address,
            auth,
            stream=True,
            headers={HTTP_HEADER_PROXY_ASSET: True}
        )

        if not r.ok:
            return Response({
                'message': f'Cannot proxify asset from node {asset["owner"]}: {str(r.text)}'
            }, status=r.status_code)

        response = CustomFileResponse(
            streaming_content=(chunk for chunk in r.iter_content(512 * 1024)),
            status=r.status_code)

        for header in r.headers:
            # We don't use hop_by_hop headers since they are incompatible
            # with WSGI
            if not is_hop_by_hop(header):
                response[header] = r.headers.get(header)

        return response


def validate_key(key):
    try:
        uuid.UUID(key)
    except ValueError:
        raise exceptions.BadRequestError(f'key is not a valid UUID: "{key}"')


def validate_sort(sort):
    if sort not in ['asc', 'desc']:
        raise exceptions.BadRequestError(f"Invalid sort value (must be either 'desc' or 'asc'): {sort}")


class LedgerException(Exception):
    def __init__(self, data, st):
        self.data = data
        self.st = st
        super(LedgerException).__init__()


class ValidationException(Exception):
    def __init__(self, data, key, st):
        self.data = data
        self.key = key
        self.st = st
        super(ValidationException).__init__()


def get_success_create_code():
    if settings.LEDGER_SYNC_ENABLED:
        return status.HTTP_201_CREATED
    else:
        return status.HTTP_202_ACCEPTED


def get_channel_name(request):

    if hasattr(request.user, 'channel'):
        return request.user.channel.name

    if 'Substra-Channel-Name' in request.headers:
        return request.headers['Substra-Channel-Name']

    raise exceptions.BadRequestError('Could not determine channel name')


def is_proxied_request(request) -> bool:
    """Return True if the API consumer is another backend-server node proxying a user request.

    :param request: incoming HTTP request
    """
    return HTTP_HEADER_PROXY_ASSET in request.headers

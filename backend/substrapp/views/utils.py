import os
import uuid

from django.http import FileResponse, HttpResponse
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings

from node.authentication import NodeUser
from substrapp.ledger.api import get_object_from_ledger
from substrapp.ledger.exceptions import LedgerError
from substrapp.minio.connection import get_minio_client
from substrapp.utils import NodeError, get_remote_file, get_owner, get_remote_file_content
from node.models import OutgoingNode

from django.conf import settings
from rest_framework import status
from requests.auth import HTTPBasicAuth
from wsgiref.util import is_hop_by_hop

from substrapp import exceptions


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

    def has_access(self, user, asset):
        """Returns true if API consumer can access asset data."""
        if user.is_anonymous:  # safeguard, should never happened
            return False

        permission = asset['permissions']['process']

        if type(user) is NodeUser:  # for node
            node_id = user.username
        else:  # for classic user, test on current msp id
            node_id = get_owner()

        return permission['public'] or node_id in permission['authorized_ids']

    def download_file(self, request, django_field, ledger_field=None):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        try:
            asset = get_object_from_ledger(get_channel_name(request), key, self.ledger_query_call)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        if not self.has_access(request.user, asset):
            return Response({'message': 'Unauthorized'},
                            status=status.HTTP_403_FORBIDDEN)

        if not ledger_field:
            ledger_field = django_field

        if get_owner() == asset['owner']:
            response = self._download_local_file(django_field)
        else:
            response = self._download_remote_file(get_channel_name(request), ledger_field, asset)

        return response

    def download_local_file(self, request, django_field, ledger_field=None):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        try:
            asset = get_object_from_ledger(get_channel_name(request), key, self.ledger_query_call)
        except LedgerError as e:
            return HttpResponse({'message': str(e.msg)}, status=e.status)

        if not self.has_access(request.user, asset):
            return HttpResponse({'message': 'Unauthorized'},
                                status=status.HTTP_403_FORBIDDEN)

        if not ledger_field:
            ledger_field = django_field

        return self._download_local_file(django_field)

    def _download_local_file(self, django_field):
        obj = self.get_object()
        data = getattr(obj, django_field)
        client = get_minio_client()
        path = str(data)
        f = client.get_object('my-test-bucket', path)
        response = CustomFileResponse(
            f.stream(24 * 1024),
            as_attachment=True,
            filename=os.path.basename(path)
        )
        return response

    def _download_remote_file(self, channel_name, ledger_field, asset):
        node_id = asset['owner']
        auth = authenticate_outgoing_request(node_id)
        r = get_remote_file(channel_name, asset[ledger_field]['storage_address'], auth, stream=True)
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

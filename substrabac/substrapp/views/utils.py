import os

import base64
import binascii
from importlib import import_module

from django.http import FileResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, get_authorization_header
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from substrapp.ledger_utils import get_object_from_ledger, LedgerError
from substrapp.utils import NodeError, get_remote_file, get_owner, get_remote_file_content
from node.models import OutgoingNode

from django.conf import settings
from rest_framework import status
from requests.auth import HTTPBasicAuth
from wsgiref.util import is_hop_by_hop

from django.utils.translation import ugettext_lazy as _

from rest_framework import HTTP_HEADER_ENCODING, exceptions


def authenticate_outgoing_request(outgoing_node_id):
    try:
        outgoing = OutgoingNode.objects.get(node_id=outgoing_node_id)
    except OutgoingNode.DoesNotExist:
        raise NodeError(f'Unauthorized to call remote node with node_id: {outgoing_node_id}')

    # to authenticate to remote node we use the current node id
    # with the associated outgoing secret.
    current_node_id = get_owner()

    return HTTPBasicAuth(current_node_id, outgoing.secret)


def get_remote_asset(url, node_id, content_hash, salt=None):
    auth = authenticate_outgoing_request(node_id)
    return get_remote_file_content(url, auth, content_hash, salt=salt)


class CustomFileResponse(FileResponse):
    def set_headers(self, filelike):
        super(CustomFileResponse, self).set_headers(filelike)

        self['Access-Control-Expose-Headers'] = 'Content-Disposition'


def is_local_user(user):
    return user.username == settings.BASICAUTH_USERNAME


class BasicAuthentication(BasicAuthentication):
    def authenticate(self, request):
        """
        Returns a `User` if a correct username and password have been supplied
        using HTTP Basic authentication.  Otherwise returns `None`.
        """
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'basic':
            if not settings.DEBUG:
                return None
            else:
                # create fake auth in debug mode, if no provided (user case, not node)
                debug_basic_auth = f'{settings.BASICAUTH_USERNAME}:{settings.BASICAUTH_PASSWORD}'
                auth = [b'Basic', base64.b64encode(debug_basic_auth.encode(HTTP_HEADER_ENCODING))]

        if len(auth) == 1:
            msg = _('Invalid basic header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid basic header. Credentials string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            auth_parts = base64.b64decode(auth[1]).decode(HTTP_HEADER_ENCODING).partition(':')
        except (TypeError, UnicodeDecodeError, binascii.Error):
            msg = _('Invalid basic header. Credentials not correctly base64 encoded.')
            raise exceptions.AuthenticationFailed(msg)

        userid, password = auth_parts[0], auth_parts[2]
        return self.authenticate_credentials(userid, password, request)

    def authenticate_header(self, request):
        if not settings.DEBUG:
            return 'Basic realm="%s"' % self.www_authenticate_realm

        # do not prompt basic auth prompt in debug mode
        return ''


def node_has_process_permission(asset):
    """Check if current node can process input asset."""
    permission = asset['permissions']['process']
    return permission['public'] or get_owner() in permission['authorizedIDs']


class PermissionMixin(object):

    authentication_classes = [import_module(settings.BASIC_AUTHENTICATION_MODULE).BasicAuthentication,
                              SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def _has_access(self, user, asset):
        """Returns true if API consumer can access asset data."""
        if user.is_anonymous:  # safeguard, should never happened
            return False

        if is_local_user(user):
            return True

        permission = asset['permissions']['process']
        if permission['public']:
            return True

        node_id = user.username
        return node_id in permission['authorizedIDs']

    def download_file(self, request, django_field, ledger_field=None):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            asset = get_object_from_ledger(pk, self.ledger_query_call)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        if not self._has_access(request.user, asset):
            return Response({'message': 'Unauthorized'},
                            status=status.HTTP_403_FORBIDDEN)

        if get_owner() == asset['owner']:
            obj = self.get_object()
            data = getattr(obj, django_field)
            response = CustomFileResponse(
                open(data.path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(data.path)
            )
        else:
            node_id = asset['owner']
            auth = authenticate_outgoing_request(node_id)
            if not ledger_field:
                ledger_field = django_field
            r = get_remote_file(asset[ledger_field]['storageAddress'], auth, stream=True)
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


def find_primary_key_error(validation_error, key_name='pkhash'):
    detail = validation_error.detail

    def find_unique_error(detail_dict):
        for key, errors in detail_dict.items():
            if key != key_name:
                continue
            for error in errors:
                if error.code == 'unique':
                    return error

        return None

    # according to the rest_framework documentation,
    # validation_error.detail could be either a dict, a list or a nested
    # data structure

    if isinstance(detail, dict):
        return find_unique_error(detail)
    elif isinstance(detail, list):
        for sub_detail in detail:
            if isinstance(sub_detail, dict):
                unique_error = find_unique_error(sub_detail)
                if unique_error is not None:
                    return unique_error

    return None


def validate_pk(pk):
    if len(pk) != 64:
        raise Exception(f'Wrong pk {pk}')

    try:
        int(pk, 16)  # test if pk is correct (hexadecimal)
    except ValueError:
        raise Exception(f'Wrong pk {pk}')


def validate_sort(sort):
    if sort not in ['asc', 'desc']:
        raise Exception(f"Invalid sort value (must be either 'desc' or 'asc'): {sort}")


class LedgerException(Exception):
    def __init__(self, data, st):
        self.data = data
        self.st = st
        super(LedgerException).__init__()


class ValidationException(Exception):
    def __init__(self, data, pkhash, st):
        self.data = data
        self.pkhash = pkhash
        self.st = st
        super(ValidationException).__init__()


def get_success_create_code():
    if getattr(settings, 'LEDGER_SYNC_ENABLED'):
        return status.HTTP_201_CREATED
    else:
        return status.HTTP_202_ACCEPTED

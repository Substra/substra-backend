import functools
import os
import tempfile

import mock
import requests
from requests.auth import HTTPBasicAuth
from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.views.utils import PermissionMixin


class MockRequest:
    user = None


def with_permission_mixin(remote, same_file_property, has_access):
    def inner(f):
        @functools.wraps(f)
        def wrapper(self):
            ledger_value = {
                'owner': 'owner-foo',
                'file_property' if same_file_property else 'ledger_file_property': {
                    'storageAddress': 'foo'
                }
            }
            with mock.patch('substrapp.views.utils.get_object_from_ledger',
                            return_value=ledger_value), \
                    tempfile.NamedTemporaryFile() as tmp_file, \
                    mock.patch('substrapp.views.utils.get_owner',
                               return_value='not-owner-foo' if remote else 'owner-foo'):
                tmp_file_content = b'foo bar'
                tmp_file.write(tmp_file_content)
                tmp_file.seek(0)

                class TestFieldFile:
                    path = tmp_file.name

                class TestModel:
                    file_property = TestFieldFile()

                permission_mixin = PermissionMixin()
                permission_mixin.get_object = mock.MagicMock(return_value=TestModel())
                permission_mixin.has_access = mock.MagicMock(return_value=has_access)
                permission_mixin.lookup_url_kwarg = 'foo'
                permission_mixin.kwargs = {'foo': 'bar'}
                permission_mixin.ledger_query_call = 'foo'

                kwargs = {
                    'tmp_file': tmp_file,
                    'content': tmp_file_content,
                    'filename': os.path.basename(tmp_file.name)
                }

                f(self, permission_mixin, **kwargs)
        return wrapper
    return inner


def with_requests_mock(allowed):
    def inner(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            tmp_file = kwargs['tmp_file']
            filename = kwargs['filename']

            requests_response = requests.Response()
            if allowed:
                requests_response.raw = tmp_file
                requests_response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                requests_response.status_code = status.HTTP_200_OK
            else:
                requests_response._content = b'{"message": "nope"}'
                requests_response.status_code = status.HTTP_401_UNAUTHORIZED

            kwargs['requests_response'] = requests_response

            with mock.patch('substrapp.views.utils.authenticate_outgoing_request',
                            return_value=HTTPBasicAuth('foo', 'bar')), \
                    mock.patch('substrapp.utils.requests.get', return_value=requests_response):
                f(*args, **kwargs)
        return wrapper
    return inner


class PermissionMixinDownloadFileTests(APITestCase):
    @with_permission_mixin(remote=False, same_file_property=False, has_access=True)
    def test_download_file_local_allowed(self, permission_mixin, content, filename, **kwargs):
        res = permission_mixin.download_file(MockRequest(),
                                             'file_property',
                                             'ledger_file_property')
        res_content = b''.join(list(res.streaming_content))
        self.assertEqual(res_content, content)
        self.assertEqual(res['Content-Disposition'], f'attachment; filename="{filename}"')
        self.assertTrue(permission_mixin.get_object.called)

    @with_permission_mixin(remote=False, same_file_property=True, has_access=False)
    def test_download_file_local_denied(self, permission_mixin, **kwargs):
        res = permission_mixin.download_file(MockRequest(), 'file_property')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    @with_permission_mixin(remote=True, same_file_property=False, has_access=True)
    @with_requests_mock(allowed=True)
    def test_download_file_remote_allowed(self, permission_mixin, content, filename, **kwargs):
        res = permission_mixin.download_file(MockRequest(),
                                             'file_property',
                                             'ledger_file_property')
        res_content = b''.join(list(res.streaming_content))
        self.assertEqual(res_content, content)
        self.assertEqual(res['Content-Disposition'], f'attachment; filename="{filename}"')
        self.assertFalse(permission_mixin.get_object.called)

    @with_permission_mixin(remote=True, same_file_property=False, has_access=True)
    @with_requests_mock(allowed=False)
    def test_download_file_remote_denied(self, permission_mixin, **kwargs):
        res = permission_mixin.download_file(MockRequest(),
                                             'file_property',
                                             'ledger_file_property')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(permission_mixin.get_object.called)

    @with_permission_mixin(remote=True, same_file_property=True, has_access=True)
    @with_requests_mock(allowed=True)
    def test_download_file_remote_same_file_property(self, permission_mixin, content, filename,
                                                     **kwargs):
        res = permission_mixin.download_file(MockRequest(), 'file_property')
        res_content = b''.join(list(res.streaming_content))
        self.assertEqual(res_content, content)
        self.assertEqual(res['Content-Disposition'], f'attachment; filename="{filename}"')
        self.assertFalse(permission_mixin.get_object.called)

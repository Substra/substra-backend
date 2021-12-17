import functools
import os
import tempfile
import uuid
from unittest import mock

import requests
from django.core.files.storage import FileSystemStorage
from django.test import override_settings
from requests.auth import HTTPBasicAuth
from rest_framework import status
from rest_framework.test import APITestCase

from orchestrator.client import OrchestratorClient
from substrapp.views.utils import AssetPermissionError
from substrapp.views.utils import PermissionMixin
from substrapp.views.utils import if_true


class MockRequest:
    user = None
    headers = {"Substra-Channel-Name": "mychannel"}


def with_permission_mixin(remote, same_file_property, has_access):
    def inner(f):
        @functools.wraps(f)
        def wrapper(self):
            orchestrator_value = {
                "owner": "owner-foo",
                "file_property" if same_file_property else "orchestrator_file_property": {"storage_address": "foo"},
            }

            with mock.patch.object(
                OrchestratorClient, "query_algo", return_value=orchestrator_value
            ), tempfile.NamedTemporaryFile() as tmp_file, mock.patch(
                "substrapp.views.utils.get_owner",
                return_value="not-owner-foo" if remote else "owner-foo",
            ):
                tmp_file_content = b"foo bar"
                tmp_file.write(tmp_file_content)
                tmp_file.seek(0)

                class TestFieldFile:
                    path = tmp_file.name
                    storage = FileSystemStorage()

                class TestModel:
                    file_property = TestFieldFile()

                permission_mixin = PermissionMixin()
                permission_mixin.get_object = mock.MagicMock(return_value=TestModel())
                if has_access:
                    permission_mixin.check_access = mock.MagicMock()
                else:
                    permission_mixin.check_access = mock.MagicMock(side_effect=AssetPermissionError())
                permission_mixin.lookup_url_kwarg = "foo"
                permission_mixin.kwargs = {"foo": str(uuid.uuid4())}
                permission_mixin.ledger_query_call = "foo"

                kwargs = {
                    "tmp_file": tmp_file,
                    "content": tmp_file_content,
                    "filename": os.path.basename(tmp_file.name),
                }

                f(self, permission_mixin, **kwargs)

        return wrapper

    return inner


def with_requests_mock(allowed):
    def inner(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            tmp_file = kwargs["tmp_file"]
            filename = kwargs["filename"]

            requests_response = requests.Response()
            if allowed:
                requests_response.raw = tmp_file
                requests_response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
                requests_response.status_code = status.HTTP_200_OK
            else:
                requests_response._content = b'{"message": "nope"}'
                requests_response.status_code = status.HTTP_401_UNAUTHORIZED

            kwargs["requests_response"] = requests_response

            with mock.patch(
                "substrapp.views.utils.authenticate_outgoing_request",
                return_value=HTTPBasicAuth("foo", "bar"),
            ), mock.patch("substrapp.utils.requests.get", return_value=requests_response):
                f(*args, **kwargs)

        return wrapper

    return inner


@override_settings(LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}})
class PermissionMixinDownloadFileTests(APITestCase):
    @with_permission_mixin(remote=False, same_file_property=False, has_access=True)
    def test_download_file_local_allowed(self, permission_mixin, content, filename, **kwargs):
        res = permission_mixin.download_file(MockRequest(), "query_algo", "file_property", "orchestrator_file_property")
        res_content = b"".join(list(res.streaming_content))
        self.assertEqual(res_content, content)
        self.assertEqual(res["Content-Disposition"], f'attachment; filename="{filename}"')
        self.assertTrue(permission_mixin.get_object.called)

    @with_permission_mixin(remote=False, same_file_property=True, has_access=False)
    def test_download_file_local_denied(self, permission_mixin, **kwargs):
        res = permission_mixin.download_file(MockRequest(), "query_algo", "file_property")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    @with_permission_mixin(remote=True, same_file_property=False, has_access=True)
    @with_requests_mock(allowed=True)
    def test_download_file_remote_allowed(self, permission_mixin, content, filename, **kwargs):
        res = permission_mixin.download_file(MockRequest(), "query_algo", "file_property", "orchestrator_file_property")
        res_content = b"".join(list(res.streaming_content))
        self.assertEqual(res_content, content)
        self.assertEqual(res["Content-Disposition"], f'attachment; filename="{filename}"')
        self.assertFalse(permission_mixin.get_object.called)

    @with_permission_mixin(remote=True, same_file_property=False, has_access=True)
    @with_requests_mock(allowed=False)
    def test_download_file_remote_denied(self, permission_mixin, **kwargs):
        res = permission_mixin.download_file(MockRequest(), "query_algo", "file_property", "orchestrator_file_property")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(permission_mixin.get_object.called)

    @with_permission_mixin(remote=True, same_file_property=True, has_access=True)
    @with_requests_mock(allowed=True)
    def test_download_file_remote_same_file_property(self, permission_mixin, content, filename, **kwargs):
        res = permission_mixin.download_file(MockRequest(), "query_algo", "file_property")
        res_content = b"".join(list(res.streaming_content))
        self.assertEqual(res_content, content)
        self.assertEqual(res["Content-Disposition"], f'attachment; filename="{filename}"')
        self.assertFalse(permission_mixin.get_object.called)


def test_if_true():
    def double(func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            return func(*args, **kwargs) * 2

        return wrapper_func

    @if_true(double, False)
    def not_decorated_func(x):
        return x

    @if_true(double, True)
    def decorated_func(x):
        return x

    assert not_decorated_func(1) == 1
    assert decorated_func(1) == 2
    assert not_decorated_func.__name__ == "not_decorated_func"
    assert decorated_func.__name__ == "decorated_func"

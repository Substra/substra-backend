import os
import shutil
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.tests import asset_factory as factory
from api.tests.common import generate_basic_auth_header
from organization.models import IncomingOrganization
from organization.models import OutgoingOrganization
from substrapp.models import Function as FunctionFiles
from substrapp.tests.common import get_description_function
from substrapp.tests.common import get_sample_function

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class AuthenticationTests(APITestCase):
    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        # create function instance which file download is protected
        self.function_file, self.function_filename = get_sample_function()
        self.function_description_file, self.function_description_filename = get_description_function()
        self.function = FunctionFiles.objects.create(
            file=self.function_file, description=self.function_description_file
        )
        metadata = factory.create_function(key=self.function.key, public=True, owner="foo")
        metadata.function_address = "http://fake_address.com"
        metadata.save()
        self.function_url = reverse("api:function-file", kwargs={"pk": self.function.key})

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        cls.incoming_organization = IncomingOrganization.objects.create(
            organization_id="external_organization_id", password="s3cr37"
        )
        cls.outgoing_organization = OutgoingOrganization.objects.create(
            organization_id="external_organization_id", secret="s3cr37"
        )
        user, created = User.objects.get_or_create(username="foo")
        if created:
            user.set_password("bar")
            user.save()
        cls.user = user

    def test_authentication_fail(self):
        response = self.client.get(self.function_url, **self.extra)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_authentication_internal(self):
        authorization_header = generate_basic_auth_header(
            self.outgoing_organization.organization_id, self.outgoing_organization.secret
        )

        self.client.credentials(HTTP_AUTHORIZATION=authorization_header)

        with mock.patch("api.views.utils.get_owner", return_value="foo"):
            response = self.client.get(self.function_url, **self.extra)

            self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_authentication_with_bad_settings_credentials_fail(self):
        authorization_header = generate_basic_auth_header("unauthorized_username", "unauthorized_password")

        self.client.credentials(HTTP_AUTHORIZATION=authorization_header)
        response = self.client.get(self.function_url, **self.extra)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_authentication_with_organization(self):
        authorization_header = generate_basic_auth_header("external_organization_id", "s3cr37")

        self.client.credentials(HTTP_AUTHORIZATION=authorization_header)

        with mock.patch("api.views.utils.get_owner", return_value="foo"):
            response = self.client.get(self.function_url, **self.extra)

            self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_authentication_with_organization_fail(self):
        bad_authorization_headers = [
            generate_basic_auth_header("external_organization_id", "bad_s3cr37"),
            generate_basic_auth_header("bad_external_organization_id", "s3cr37"),
            generate_basic_auth_header("bad_external_organization_id", "bad_s3cr37"),
        ]

        for header in bad_authorization_headers:
            self.client.credentials(HTTP_AUTHORIZATION=header)
            response = self.client.get(self.function_url, **self.extra)

            self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_obtain_token(self):
        endpoint = "/api-token-auth/?note=&expiry=never"
        # clean use
        response = self.client.post(endpoint, {"username": "foo", "password": "baz"}, **self.extra)
        self.assertEqual(response.status_code, 400)

        response = self.client.post(endpoint, {"username": "foo", "password": "bar"}, **self.extra)
        self.assertEqual(response.status_code, 200)
        token_old = response.json()["token"]
        self.assertTrue(token_old)

        # token should be update after a second post
        response = self.client.post(endpoint, {"username": "foo", "password": "bar"}, **self.extra)
        self.assertEqual(response.status_code, 200)
        token = response.json()["token"]
        self.assertTrue(token)

        # tokens should be different
        self.assertNotEqual(token_old, token)

        # test tokens validity

        valid_auth_token_header = f"Token {token}"
        self.client.credentials(HTTP_AUTHORIZATION=valid_auth_token_header)

        with mock.patch("api.views.utils.get_owner", return_value="foo"):
            response = self.client.get(self.function_url, **self.extra)

            self.assertEqual(status.HTTP_200_OK, response.status_code)

        # usage with an existing token
        # the token should be ignored since the purpose of the view is to authenticate via user/password
        valid_auth_token_header = f"Token {token}"
        self.client.credentials(HTTP_AUTHORIZATION=valid_auth_token_header)
        response = self.client.post(endpoint, {"username": "foo", "password": "bar"}, **self.extra)
        self.assertEqual(response.status_code, 200)

        invalid_auth_token_header = "Token nope"
        self.client.credentials(HTTP_AUTHORIZATION=invalid_auth_token_header)
        response = self.client.post(endpoint, {"username": "foo", "password": "bar"}, **self.extra)
        self.assertEqual(response.status_code, 200)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TestLoginCase(APITestCase):
    login_url = "/me/login/"
    logout_url = "/me/logout/"
    refresh_url = "/me/refresh/"

    username = "foo"
    password = "bar"

    extra = {"HTTP_ACCEPT": "application/json;version=0.0"}

    @classmethod
    def setUpTestData(cls):
        user, created = User.objects.get_or_create(username=cls.username)
        if created:
            user.set_password(cls.password)
            user.save()
        cls.user = user

    def _login(self):
        data = {"username": self.username, "password": self.password}
        r = self.client.post(self.login_url, data, **self.extra)

        return r.status_code, r

    def test_logout_response_200(self):
        _, login_response = self._login()
        self.assertEqual(status.HTTP_200_OK, login_response.status_code)

        response = self.client.post(self.refresh_url, cookies=login_response.cookies)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response = self.client.get(self.logout_url, cookies=login_response.cookies)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response = self.client.post(self.refresh_url, cookies=login_response.cookies)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

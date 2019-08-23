import base64

from rest_framework import status
from rest_framework.test import APITestCase
from node.models import IncomingNode

from ..common import generate_basic_auth_header
from django.conf import settings


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

    @classmethod
    def setUpTestData(cls):
        cls.incoming_node = IncomingNode.objects.create(node_id="external_node_id", secret="s3cr37")

    def test_authentication_fail(self):
        response = self.client.get('/', **self.extra)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_authentication_with_settings_success(self):
        authorization_header = generate_basic_auth_header(settings.BASICAUTH_USERNAME, settings.BASICAUTH_PASSWORD)

        self.client.credentials(HTTP_AUTHORIZATION=authorization_header)
        response = self.client.get('/', **self.extra)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_authentication_with_bad_settings_credentials_fail(self):
        authorization_header = generate_basic_auth_header('unauthorized_username', 'unauthorized_password')

        self.client.credentials(HTTP_AUTHORIZATION=authorization_header)
        response = self.client.get('/', **self.extra)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_authentication_with_node(self):
        authorization_header = generate_basic_auth_header('external_node_id', 's3cr37')

        self.client.credentials(HTTP_AUTHORIZATION=authorization_header)
        response = self.client.get('/', **self.extra)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_authentication_with_node_fail(self):
        bad_authorization_headers = [
            generate_basic_auth_header('external_node_id', 'bad_s3cr37'),
            generate_basic_auth_header('bad_external_node_id', 's3cr37'),
            generate_basic_auth_header('bad_external_node_id', 'bad_s3cr37'),
        ]

        for header in bad_authorization_headers:
            self.client.credentials(HTTP_AUTHORIZATION=header)
            response = self.client.get('/', **self.extra)

            self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

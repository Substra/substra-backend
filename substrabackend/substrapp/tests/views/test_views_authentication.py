import mock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from node.models import IncomingNode
from substrapp.models import Algo

from ..common import generate_basic_auth_header, get_sample_algo_metadata, get_sample_algo, get_description_algo
from django.conf import settings


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        # create algo instance which file download is protected
        self.algo_file, self.algo_filename = get_sample_algo()
        self.algo_description_file, self.algo_description_filename = get_description_algo()
        self.algo = Algo.objects.create(file=self.algo_file, description=self.algo_description_file)
        self.algo_url = reverse('substrapp:algo-file', kwargs={'pk': self.algo.pk})

    @classmethod
    def setUpTestData(cls):
        cls.incoming_node = IncomingNode.objects.create(node_id="external_node_id", secret="s3cr37")

    def test_authentication_fail(self):
        response = self.client.get(self.algo_url, **self.extra)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_authentication_with_settings_success(self):
        authorization_header = generate_basic_auth_header(settings.BASICAUTH_USERNAME, settings.BASICAUTH_PASSWORD)

        self.client.credentials(HTTP_AUTHORIZATION=authorization_header)

        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch('substrapp.views.utils.get_object_from_ledger') \
                as mget_object_from_ledger:
            mget_object_from_ledger.return_value = get_sample_algo_metadata()
            response = self.client.get(self.algo_url, **self.extra)

            self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_authentication_with_bad_settings_credentials_fail(self):
        authorization_header = generate_basic_auth_header('unauthorized_username', 'unauthorized_password')

        self.client.credentials(HTTP_AUTHORIZATION=authorization_header)
        response = self.client.get(self.algo_url, **self.extra)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_authentication_with_node(self):
        authorization_header = generate_basic_auth_header('external_node_id', 's3cr37')

        self.client.credentials(HTTP_AUTHORIZATION=authorization_header)

        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch('substrapp.views.utils.get_object_from_ledger') \
                as mget_object_from_ledger:
            mget_object_from_ledger.return_value = get_sample_algo_metadata()
            response = self.client.get(self.algo_url, **self.extra)

            self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_authentication_with_node_fail(self):
        bad_authorization_headers = [
            generate_basic_auth_header('external_node_id', 'bad_s3cr37'),
            generate_basic_auth_header('bad_external_node_id', 's3cr37'),
            generate_basic_auth_header('bad_external_node_id', 'bad_s3cr37'),
        ]

        for header in bad_authorization_headers:
            self.client.credentials(HTTP_AUTHORIZATION=header)
            response = self.client.get(self.algo_url, **self.extra)

            self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

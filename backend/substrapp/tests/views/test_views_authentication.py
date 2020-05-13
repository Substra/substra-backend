import mock
from django.contrib.auth.models import User
from django.urls import reverse
import os
import shutil
from rest_framework import status
from rest_framework.test import APITestCase
from node.models import IncomingNode, OutgoingNode
from substrapp.models import Algo

from ..common import generate_basic_auth_header, get_sample_algo_metadata, get_sample_algo, get_description_algo
from django.test import override_settings

MEDIA_ROOT = "/tmp/unittests_views/"


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AuthenticationTests(APITestCase):
    def setUp(self):

        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        # create algo instance which file download is protected
        self.algo_file, self.algo_filename = get_sample_algo()
        self.algo_description_file, self.algo_description_filename = get_description_algo()
        self.algo = Algo.objects.create(file=self.algo_file, description=self.algo_description_file)
        self.algo_url = reverse('substrapp:algo-file', kwargs={'pk': self.algo.pk})

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        cls.incoming_node = IncomingNode.objects.create(node_id="external_node_id", secret="s3cr37")
        cls.outgoing_node = OutgoingNode.objects.create(node_id="external_node_id", secret="s3cr37")
        user, created = User.objects.get_or_create(username='foo')
        if created:
            user.set_password('bar')
            user.save()
        cls.user = user

    def test_authentication_fail(self):
        response = self.client.get(self.algo_url, **self.extra)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_authentication_internal(self):
        authorization_header = generate_basic_auth_header(self.outgoing_node.node_id, self.outgoing_node.secret)

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

    def test_obtain_token(self):
        # clean use
        response = self.client.post('/api-token-auth/',
                                    {'username': 'foo', 'password': 'baz'}, **self.extra)
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/api-token-auth/',
                                    {'username': 'foo', 'password': 'bar'}, **self.extra)
        self.assertEqual(response.status_code, 200)
        token_old = response.json()['token']
        self.assertTrue(token_old)

        # token should be update after a second post
        response = self.client.post('/api-token-auth/',
                                    {'username': 'foo', 'password': 'bar'}, **self.extra)
        self.assertEqual(response.status_code, 200)
        token = response.json()['token']
        self.assertTrue(token)

        # tokens should be different
        self.assertNotEqual(token_old, token)

        # test tokens validity
        invalid_auth_token_header = f"Token {token_old}"
        self.client.credentials(HTTP_AUTHORIZATION=invalid_auth_token_header)

        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch('substrapp.views.utils.get_object_from_ledger') \
                as mget_object_from_ledger:
            mget_object_from_ledger.return_value = get_sample_algo_metadata()
            response = self.client.get(self.algo_url, **self.extra)

            self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

        valid_auth_token_header = f"Token {token}"
        self.client.credentials(HTTP_AUTHORIZATION=valid_auth_token_header)

        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch('substrapp.views.utils.get_object_from_ledger') \
                as mget_object_from_ledger:
            mget_object_from_ledger.return_value = get_sample_algo_metadata()
            response = self.client.get(self.algo_url, **self.extra)

            self.assertEqual(status.HTTP_200_OK, response.status_code)

        # usage with an existing token
        # the token should be ignored since the purpose of the view is to authenticate via user/password
        valid_auth_token_header = f"Token {token}"
        self.client.credentials(HTTP_AUTHORIZATION=valid_auth_token_header)
        response = self.client.post('/api-token-auth/',
                                    {'username': 'foo', 'password': 'bar'}, **self.extra)
        self.assertEqual(response.status_code, 200)

        invalid_auth_token_header = 'Token nope'
        self.client.credentials(HTTP_AUTHORIZATION=invalid_auth_token_header)
        response = self.client.post('/api-token-auth/',
                                    {'username': 'foo', 'password': 'bar'}, **self.extra)
        self.assertEqual(response.status_code, 200)

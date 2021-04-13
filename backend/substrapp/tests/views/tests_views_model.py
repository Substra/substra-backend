import os
import shutil
import logging

import mock

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from node.authentication import NodeUser

from substrapp.ledger.exceptions import LedgerError
from substrapp.views.model import ModelPermissionViewSet
from substrapp.views.utils import PermissionError

from ..common import get_sample_model, AuthenticatedClient, encode_filter
from ..assets import objective, datamanager, algo, model


MEDIA_ROOT = "/tmp/unittests_views/"
CHANNEL = 'mychannel'
TEST_ORG = 'MyTestOrg'
MODEL_KEY = 'some-key'


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT, LEDGER_MSP_ID=TEST_ORG)
class ModelViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.model, self.model_filename = get_sample_model()

        self.extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': CHANNEL,
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        self.logger = logging.getLogger('django.request')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_model_list_empty(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [[], ['ISIC']]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, ['ISIC'])

    def test_model_list_filter_fail(self):

        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = model

            url = reverse('substrapp:model-list')
            search_params = '?search=modeERRORl'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertIn('Malformed search filters', r['message'])

    def test_model_list_filter_key(self):

        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = model

            key = model[1]['traintuple']['key']
            url = reverse('substrapp:model-list')
            search_params = f'?search=model%253Akey%253A{key}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(len(r), 1)

    def test_model_list_filter_datamanager(self):

        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = model
            mquery_ledger2.return_value = datamanager

            search_params = f'?search=dataset%253Aname%253A{encode_filter(datamanager[0]["name"])}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 14)

    def test_model_list_filter_objective(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = model
            mquery_ledger2.return_value = objective

            search_params = f'?search=objective%253Aname%253A{encode_filter(objective[0]["name"])}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 4)

    def test_model_list_filter_algo(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = model
            mquery_ledger2.return_value = algo

            search_params = f'?search=algo%253Aname%253A{encode_filter(algo[0]["name"])}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 3)

    def test_model_retrieve(self):
        done_model = [m for m in model if 'traintuple' in m and m['traintuple']['status'] == 'done'][0]

        with mock.patch('substrapp.views.model.get_object_from_ledger') as mget_object_from_ledger, \
                mock.patch('substrapp.views.model.get_remote_asset') as get_remote_asset:
            mget_object_from_ledger.return_value = done_model

            get_remote_asset.return_value = self.model.read().encode()

            url = reverse('substrapp:model-list')
            search_params = done_model['traintuple']['out_model']['key'] + '/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(r, done_model)

    def test_model_retrieve_fail(self):

        url = reverse('substrapp:model-list')

        # Key not enough chars
        search_params = '12312323/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = 'X' * 32 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.model.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('TEST')
            response = self.client.get(f'{url}{objective[0]["key"]}/', **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_model_download_by_node_for_worker(self):
        """"Simple node-to-node download, e.g. worker downloads in-model"""
        pvs = ModelPermissionViewSet()

        pvs.check_access(
            CHANNEL,
            NodeUser(),
            {'key': MODEL_KEY, 'permissions': {'process': {'public': True}}},
            is_proxied_request=False)

        with self.assertRaises(PermissionError):
            pvs.check_access(
                CHANNEL,
                NodeUser(),
                {'key': MODEL_KEY, 'permissions': {'process': {'public': False, 'authorized_ids': []}}},
                is_proxied_request=False)

        pvs.check_access(
            CHANNEL,
            NodeUser(username='foo'),
            {'key': MODEL_KEY, 'permissions': {'process': {'public': False, 'authorized_ids': ['foo']}}},
            is_proxied_request=False)

    @override_settings(LEDGER_CHANNELS={CHANNEL: {'model_export_enabled': True}})
    def test_model_export_proxied(self):
        """Model export (proxied) with option enabled"""
        pvs = ModelPermissionViewSet()

        pvs.check_access(
            CHANNEL,
            NodeUser(),
            {'key': MODEL_KEY, 'permissions': {'download': {'public': True}}},
            is_proxied_request=True)

        with self.assertRaises(PermissionError):
            pvs.check_access(
                CHANNEL,
                NodeUser(),
                {'key': MODEL_KEY, 'permissions': {'download': {'public': False, 'authorized_ids': []}}},
                is_proxied_request=True)

        pvs.check_access(
            CHANNEL,
            NodeUser(username='foo'),
            {'key': MODEL_KEY, 'permissions': {'download': {'public': False, 'authorized_ids': ['foo']}}},
            is_proxied_request=True)

    @override_settings(LEDGER_CHANNELS={CHANNEL: {'model_export_enabled': False}})
    def test_model_download_by_node_proxied_option_disabled(self):
        """Model export (proxied) with option disabled"""
        pvs = ModelPermissionViewSet()

        with self.assertRaises(PermissionError):
            pvs.check_access(
                CHANNEL,
                NodeUser(),
                {'key': MODEL_KEY, 'permissions': {'download': {'public': True}}},
                is_proxied_request=True)

    @override_settings(LEDGER_CHANNELS={CHANNEL: {'model_export_enabled': True}})
    def test_model_download_by_classic_user_enabled(self):
        """Model export (by end-user, not proxied) with option enabled"""
        pvs = ModelPermissionViewSet()

        pvs.check_access(
            CHANNEL,
            User(),
            {'key': MODEL_KEY, 'permissions': {'download': {'public': True}}},
            is_proxied_request=False)

        with self.assertRaises(PermissionError):
            pvs.check_access(
                CHANNEL,
                User(),
                {'key': MODEL_KEY, 'permissions': {'download': {'public': False, 'authorized_ids': []}}},
                is_proxied_request=False)

    @override_settings(LEDGER_CHANNELS={CHANNEL: {'model_export_enabled': False}})
    def test_model_download_by_classic_user_disabled(self):
        """Model export (by end-user, not proxied) with option disabled"""
        pvs = ModelPermissionViewSet()

        with self.assertRaises(PermissionError):
            pvs.check_access(
                CHANNEL,
                User(),
                {'key': MODEL_KEY, 'permissions': {'process': {'public': True}}},
                is_proxied_request=False)

    @override_settings(LEDGER_CHANNELS={CHANNEL: {}})
    def test_model_download_by_classic_user_default(self):
        pvs = ModelPermissionViewSet()

        # Access to model download should be denied because the "model_export_enabled"
        # option is not specified in the app configuration.
        with self.assertRaises(PermissionError):
            pvs.check_access(
                CHANNEL,
                User(),
                {'key': MODEL_KEY, 'permissions': {'process': {'public': True}}},
                is_proxied_request=False)

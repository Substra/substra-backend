import copy
import os
import shutil
import logging

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.ledger.exceptions import LedgerError


from ..common import get_sample_datamanager, AuthenticatedClient, encode_filter
from ..assets import objective, datamanager, model

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class DataManagerViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.data_description, self.data_description_filename, \
            self.data_data_opener, self.data_opener_filename = get_sample_datamanager()

        self.extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        self.logger = logging.getLogger('django.request')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_datamanager_list_empty(self):
        url = reverse('substrapp:data_manager-list')
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = []

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [])

    def test_datamanager_list_success(self):
        url = reverse('substrapp:data_manager-list')
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = datamanager

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, datamanager)

    def test_datamanager_list_filter_fail(self):
        url = reverse('substrapp:data_manager-list')
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = datamanager

            search_params = '?search=dataseERRORt'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_datamanager_list_filter_name(self):
        url = reverse('substrapp:data_manager-list')
        name_to_filter = encode_filter(datamanager[0]['name'])

        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = datamanager

            search_params = f'?search=dataset%253Aname%253A{name_to_filter}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 1)

    def test_datamanager_list_filter_objective(self):
        url = reverse('substrapp:data_manager-list')

        objective_key = datamanager[0]['objective_key']
        objective_to_filter = encode_filter([o for o in objective
                                             if o['key'] == objective_key].pop()['name'])

        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = datamanager
            mquery_ledger2.return_value = objective

            search_params = f'?search=objective%253Aname%253A{objective_to_filter}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 1)

    def test_datamanager_list_filter_model(self):
        url = reverse('substrapp:data_manager-list')
        done_model = [
            m for m in model
            if 'traintuple' in m and m['traintuple']['status'] == 'done' and m['testtuple']['traintuple_key']
        ][0]

        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = datamanager
            mquery_ledger2.return_value = model
            out_model_hash = done_model['traintuple']['out_model']['hash']
            search_params = f'?search=model%253Ahash%253A{out_model_hash}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 2)

    def test_datamanager_retrieve(self):
        url = reverse('substrapp:data_manager-list')
        datamanager_response = copy.deepcopy(datamanager[0])
        datamanager_response['key'] = '8dd01465-003a-9b1e-01c9-9c904d86aa51'
        with mock.patch('substrapp.views.datamanager.get_object_from_ledger') as mget_object_from_ledger, \
                mock.patch('substrapp.views.datamanager.get_remote_asset') as mget_remote_asset:
            mget_object_from_ledger.return_value = datamanager_response

            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'), 'rb') as f:
                opener_content = f.read()

            with open(os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    '../../../../fixtures/chunantes/datamanagers/datamanager0/description.md'), 'rb') as f:
                description_content = f.read()

            mget_remote_asset.side_effect = [opener_content, description_content]

            search_params = '8dd01465-003a-9b1e-01c9-9c904d86aa51/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(r, datamanager_response)

    def test_datamanager_retrieve_fail(self):

        url = reverse('substrapp:data_manager-list')

        # Key < 32 chars
        search_params = '12312323/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = 'X' * 32 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.datamanager.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('TEST')
            response = self.client.get(f'{url}{objective[0]["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_datamanager_list_storage_addresses_update(self):
        url = reverse('substrapp:data_manager-list')
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.datamanager.get_remote_asset') as mget_remote_asset:

            # mock content
            mget_remote_asset.return_value = b'dummy binary content'
            ledger_datamanagers = copy.deepcopy(datamanager)
            for ledger_datamanager in ledger_datamanagers:
                for field in ('description', 'opener'):
                    ledger_datamanager[field]['storage_address'] = \
                        ledger_datamanager[field]['storage_address'] \
                        .replace('http://testserver', 'http://remotetestserver')
            mquery_ledger.return_value = ledger_datamanagers

            # actual test
            res = self.client.get(url, **self.extra)
            res_datamanagers = res.data
            self.assertEqual(len(res_datamanagers), len(datamanager))
            for i, res_datamanager in enumerate(res_datamanagers):
                for field in ('description', 'opener'):
                    self.assertEqual(res_datamanager[field]['storage_address'],
                                     datamanager[i][field]['storage_address'])

    def test_datamanager_retrieve_storage_addresses_update_with_cache(self):
        url = reverse('substrapp:data_manager-detail', args=[datamanager[0]['key']])
        with mock.patch('substrapp.views.datamanager.get_object_from_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.datamanager.node_has_process_permission',
                           return_value=True), \
                mock.patch('substrapp.views.datamanager.get_remote_asset') as mget_remote_asset:

            # mock content
            mget_remote_asset.return_value = b'dummy binary content'
            ledger_datamanager = copy.deepcopy(datamanager[0])
            for field in ('description', 'opener'):
                ledger_datamanager[field]['storage_address'] = \
                    ledger_datamanager[field]['storage_address'].replace('http://testserver',
                                                                         'http://remotetestserver')
            mquery_ledger.return_value = ledger_datamanager

            # actual test
            res = self.client.get(url, **self.extra)
            for field in ('description', 'opener'):
                self.assertEqual(res.data[field]['storage_address'],
                                 datamanager[0][field]['storage_address'])

    def test_datamanager_retrieve_storage_addresses_update_without_cache(self):
        url = reverse('substrapp:data_manager-detail', args=[datamanager[0]['key']])
        with mock.patch('substrapp.views.datamanager.get_object_from_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.datamanager.node_has_process_permission',
                           return_value=False), \
                mock.patch('substrapp.views.datamanager.get_remote_asset') as mget_remote_asset:

            # mock content
            mget_remote_asset.return_value = b'dummy binary content'
            ledger_datamanager = copy.deepcopy(datamanager[0])
            for field in ('description', 'opener'):
                ledger_datamanager[field]['storage_address'] = \
                    ledger_datamanager[field]['storage_address'].replace('http://testserver',
                                                                         'http://remotetestserver')
            mquery_ledger.return_value = ledger_datamanager

            # actual test
            res = self.client.get(url, **self.extra)
            for field in ('description', 'opener'):
                self.assertEqual(res.data[field]['storage_address'],
                                 datamanager[0][field]['storage_address'])

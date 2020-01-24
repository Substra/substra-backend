import copy
import os
import shutil
import logging

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.ledger_utils import LedgerError
from substrapp.utils import get_hash


from ..common import get_sample_datamanager, AuthenticatedClient
from ..assets import objective, datamanager, model

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
@override_settings(LEDGER_SYNC_ENABLED=True)
class DataManagerViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.data_description, self.data_description_filename, \
            self.data_data_opener, self.data_opener_filename = get_sample_datamanager()

        self.extra = {
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
            self.assertEqual(r, [[]])

    def test_datamanager_list_success(self):
        url = reverse('substrapp:data_manager-list')
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = datamanager

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [datamanager])

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
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = datamanager

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_datamanager_list_filter_objective(self):
        url = reverse('substrapp:data_manager-list')
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = datamanager
            mquery_ledger2.return_value = objective

            search_params = '?search=objective%253Aname%253ASkin%2520Lesion%2520Classification%2520Objective'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_datamanager_list_filter_model(self):
        url = reverse('substrapp:data_manager-list')
        done_model = [
            m for m in model
            if 'traintuple' in m and m['traintuple']['status'] == 'done' and m['testtuple']['traintupleKey']
        ][0]

        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = datamanager
            mquery_ledger2.return_value = model
            pkhash = done_model['traintuple']['outModel']['hash']
            search_params = f'?search=model%253Ahash%253A{pkhash}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_datamanager_retrieve(self):
        url = reverse('substrapp:data_manager-list')
        datamanager_response = [d for d in datamanager
                                if d['key'] == '8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca'][0]
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

            search_params = '8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(r, datamanager_response)

    def test_datamanager_retrieve_fail(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        url = reverse('substrapp:data_manager-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.datamanager.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('TEST')

            file_hash = get_hash(os.path.join(dir_path,
                                              "../../../../fixtures/owkin/objectives/objective0/description.md"))
            search_params = f'{file_hash}/'
            response = self.client.get(url + search_params, **self.extra)
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
                    ledger_datamanager[field]['storageAddress'] = \
                        ledger_datamanager[field]['storageAddress'] \
                        .replace('http://testserver', 'http://remotetestserver')
            mquery_ledger.return_value = ledger_datamanagers

            # actual test
            res = self.client.get(url, **self.extra)
            res_datamanagers = res.data[0]
            self.assertEqual(len(res_datamanagers), len(datamanager))
            for i, res_datamanager in enumerate(res_datamanagers):
                for field in ('description', 'opener'):
                    self.assertEqual(res_datamanager[field]['storageAddress'],
                                     datamanager[i][field]['storageAddress'])

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
                ledger_datamanager[field]['storageAddress'] = \
                    ledger_datamanager[field]['storageAddress'].replace('http://testserver',
                                                                        'http://remotetestserver')
            mquery_ledger.return_value = ledger_datamanager

            # actual test
            res = self.client.get(url, **self.extra)
            for field in ('description', 'opener'):
                self.assertEqual(res.data[field]['storageAddress'],
                                 datamanager[0][field]['storageAddress'])

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
                ledger_datamanager[field]['storageAddress'] = \
                    ledger_datamanager[field]['storageAddress'].replace('http://testserver',
                                                                        'http://remotetestserver')
            mquery_ledger.return_value = ledger_datamanager

            # actual test
            res = self.client.get(url, **self.extra)
            for field in ('description', 'opener'):
                self.assertEqual(res.data[field]['storageAddress'],
                                 datamanager[0][field]['storageAddress'])

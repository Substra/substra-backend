import copy
import os
import shutil
import logging
import json

import mock
from parameterized import parameterized

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase


from substrapp.serializers import LedgerAlgoSerializer

from substrapp.ledger.exceptions import LedgerError

from ..common import get_sample_algo, AuthenticatedClient, encode_filter
from ..assets import objective, datamanager, algo, model

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AlgoViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.algo, self.algo_filename = get_sample_algo()

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

    def test_algo_list_empty(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = []

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 0, 'next': None, 'previous': None, 'results': []})

    def test_algo_list_success(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = algo

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, {'count': 5, 'next': None, 'previous': None, 'results': algo})

    def test_algo_list_filter_fail(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = algo

            search_params = '?search=algERRORo'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_algo_list_filter_name(self):
        url = reverse('substrapp:algo-list')

        name_to_filter = encode_filter(algo[0]['name'])
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = algo

            search_params = f'?search=algo%253Aname%253A{name_to_filter}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 1)
            self.assertEqual(r['count'], 1)

    def test_algo_list_filter_dual(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = algo

            search_params = f'?search=algo%253Aname%253A{encode_filter(algo[2]["name"])}'
            search_params += f'%2Calgo%253Aowner%253A{encode_filter(algo[2]["owner"])}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 1)

    def test_algo_list_filter_datamanager_fail(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = algo
            mquery_ledger2.return_value = datamanager

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_algo_list_filter_objective_fail(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = algo
            mquery_ledger2.return_value = objective

            search_params = '?search=objective%253Aname%253ASkin%2520Lesion%2520Classification%2520Objective'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_algo_list_filter_model(self):
        url = reverse('substrapp:algo-list')
        done_model = [m for m in model if 'traintuple' in m and m['traintuple']['status'] == 'done'][0]

        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = algo
            mquery_ledger2.return_value = model

            key = done_model['traintuple']['out_model']['key']
            search_params = f'?search=model%253Akey%253A{key}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r['results']), 1)

    def test_algo_retrieve(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        url = reverse('substrapp:algo-list')
        algo_response = copy.deepcopy(algo[0])
        with mock.patch('substrapp.views.algo.get_object_from_ledger') as mget_object_from_ledger, \
                mock.patch('substrapp.views.algo.get_remote_asset') as get_remote_asset:

            with open(os.path.join(dir_path,
                                   '../../../../fixtures/chunantes/algos/algo4/description.md'), 'rb') as f:
                content = f.read()
            mget_object_from_ledger.return_value = algo_response
            get_remote_asset.return_value = content

            response = self.client.get(f'{url}{algo[0]["key"]}/', **self.extra)
            r = response.json()

            self.assertEqual(r, algo_response)

    def test_algo_retrieve_fail(self):

        url = reverse('substrapp:algo-list')

        # Key not enough chars
        search_params = '12312323/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = 'X' * 32 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.algo.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('TEST')
            response = self.client.get(f'{url}{algo[0]["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_algo_create(self):
        url = reverse('substrapp:algo-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        algo_path = os.path.join(dir_path, '../../../../fixtures/chunantes/algos/algo3/algo.tar.gz')
        description_path = os.path.join(dir_path, '../../../../fixtures/chunantes/algos/algo3/description.md')

        data = {
            'json': json.dumps({
                'name': 'Logistic regression',
                'objective_key': 'some key',
                'permissions': {
                    'public': True,
                    'authorized_ids': [],
                },
            }),
            'file': open(algo_path, 'rb'),
            'description': open(description_path, 'rb'),
        }

        with mock.patch.object(LedgerAlgoSerializer, 'create') as mcreate:

            mcreate.return_value = {}
            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertIsNotNone(response.data['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data['description'].close()
        data['file'].close()

    def test_algo_list_storage_addresses_update(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.objective.get_remote_asset') as mget_remote_asset:

            # mock content
            mget_remote_asset.return_value = b'dummy binary content'
            ledger_algos = copy.deepcopy(algo)
            for ledger_algo in ledger_algos:
                for field in ('description', 'content'):
                    ledger_algo[field]['storage_address'] = \
                        ledger_algo[field]['storage_address'].replace('http://testserver',
                                                                      'http://remotetestserver')
            mquery_ledger.return_value = ledger_algos

            # actual test
            res = self.client.get(url, **self.extra)
            res_data = res.data
            res_algos = res_data['results']
            count = res_data['count']
            self.assertEqual(len(res_algos), len(algo))
            self.assertEqual(count, len(algo))
            for i, res_algo in enumerate(res_algos):
                for field in ('description', 'content'):
                    self.assertEqual(res_algo[field]['storage_address'],
                                     algo[i][field]['storage_address'])

    def test_algo_retrieve_storage_addresses_update_with_cache(self):
        url = reverse('substrapp:algo-detail', args=[algo[0]['key']])
        with mock.patch('substrapp.views.algo.get_object_from_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.algo.node_has_process_permission',
                           return_value=True), \
                mock.patch('substrapp.views.algo.get_remote_asset') as mget_remote_asset:

            # mock content
            mget_remote_asset.return_value = b'dummy binary content'
            ledger_algo = copy.deepcopy(algo[0])
            for field in ('description', 'content'):
                ledger_algo[field]['storage_address'] = \
                    ledger_algo[field]['storage_address'].replace('http://testserver',
                                                                  'http://remotetestserver')
            mquery_ledger.return_value = ledger_algo

            # actual test
            res = self.client.get(url, **self.extra)
            for field in ('description', 'content'):
                self.assertEqual(res.data[field]['storage_address'],
                                 algo[0][field]['storage_address'])

    def test_algo_retrieve_storage_addresses_update_without_cache(self):
        url = reverse('substrapp:algo-detail', args=[algo[0]['key']])
        with mock.patch('substrapp.views.algo.get_object_from_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.algo.node_has_process_permission',
                           return_value=False), \
                mock.patch('substrapp.views.algo.get_remote_asset') as mget_remote_asset:

            # mock content
            mget_remote_asset.return_value = b'dummy binary content'
            ledger_algo = copy.deepcopy(algo[0])
            for field in ('description', 'content'):
                ledger_algo[field]['storage_address'] = \
                    ledger_algo[field]['storage_address'].replace('http://testserver',
                                                                  'http://remotetestserver')
            mquery_ledger.return_value = ledger_algo

            # actual test
            res = self.client.get(url, **self.extra)
            for field in ('description', 'content'):
                self.assertEqual(res.data[field]['storage_address'],
                                 algo[0][field]['storage_address'])

    @parameterized.expand([
        ("one_page_test", 5, 1, 0, 5),
        ("one_element_per_page_page_two", 1, 2, 1, 2),
        ("two_element_per_page_page_three", 2, 3, 4, 5)
    ])
    def test_algo_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        url = reverse('substrapp:algo-list')
        url = f"{url}?page_size={page_size}&page={page_number}"
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = algo
            response = self.client.get(url, **self.extra)
        r = response.json()
        self.assertContains(response, 'count', 1)
        self.assertContains(response, 'next', 1)
        self.assertContains(response, 'previous', 1)
        self.assertContains(response, 'results', 1)
        self.assertEqual(r['results'], algo[index_down:index_up])

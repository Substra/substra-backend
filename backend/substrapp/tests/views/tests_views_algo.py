import copy
import os
import shutil
import logging
import json

import mock
import urllib.parse

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase


from substrapp.serializers import LedgerAlgoSerializer

from substrapp.ledger_utils import LedgerError

from substrapp.utils import get_hash

from ..common import get_sample_algo, AuthenticatedClient
from ..assets import objective, datamanager, algo, model

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
@override_settings(LEDGER_SYNC_ENABLED=True)
class AlgoViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.algo, self.algo_filename = get_sample_algo()

        self.extra = {
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
            self.assertEqual(r, [[]])

    def test_algo_list_success(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = algo

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [algo])

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
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = algo

            search_params = '?search=algo%253Aname%253ALogistic%2520regression'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_algo_list_filter_dual(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = algo

            search_params = f'?search=algo%253Aname%253A{urllib.parse.quote(algo[2]["name"])}'
            search_params += f'%2Calgo%253Aowner%253A{algo[2]["owner"]}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

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

            pkhash = done_model['traintuple']['outModel']['hash']
            search_params = f'?search=model%253Ahash%253A{pkhash}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_algo_retrieve(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        algo_hash = get_hash(os.path.join(dir_path, '../../../../fixtures/chunantes/algos/algo4/algo.tar.gz'))
        url = reverse('substrapp:algo-list')
        algo_response = [a for a in algo if a['key'] == algo_hash][0]
        with mock.patch('substrapp.views.algo.get_object_from_ledger') as mget_object_from_ledger, \
                mock.patch('substrapp.views.algo.get_remote_asset') as get_remote_asset:

            with open(os.path.join(dir_path,
                                   '../../../../fixtures/chunantes/algos/algo4/description.md'), 'rb') as f:
                content = f.read()
            mget_object_from_ledger.return_value = algo_response
            get_remote_asset.return_value = content

            search_params = f'{algo_hash}/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(r, algo_response)

    def test_algo_retrieve_fail(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        url = reverse('substrapp:algo-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.algo.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('TEST')

            file_hash = get_hash(os.path.join(dir_path,
                                              "../../../../fixtures/owkin/objectives/objective0/description.md"))
            search_params = f'{file_hash}/'
            response = self.client.get(url + search_params, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_algo_create(self):
        url = reverse('substrapp:algo-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        algo_path = os.path.join(dir_path, '../../../../fixtures/chunantes/algos/algo3/algo.tar.gz')
        description_path = os.path.join(dir_path, '../../../../fixtures/chunantes/algos/algo3/description.md')

        pkhash = get_hash(algo_path)

        data = {
            'json': json.dumps({
                'name': 'Logistic regression',
                'objective_key': get_hash(os.path.join(
                    dir_path, '../../../../fixtures/chunantes/objectives/objective0/description.md')),
                'permissions': {
                    'public': True,
                    'authorized_ids': [],
                }
            }),
            'file': open(algo_path, 'rb'),
            'description': open(description_path, 'rb'),
        }

        with mock.patch.object(LedgerAlgoSerializer, 'create') as mcreate:

            mcreate.return_value = {}

            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data['pkhash'], pkhash)
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
                    ledger_algo[field]['storageAddress'] = \
                        ledger_algo[field]['storageAddress'].replace('http://testserver',
                                                                     'http://remotetestserver')
            mquery_ledger.return_value = ledger_algos

            # actual test
            res = self.client.get(url, **self.extra)
            res_algos = res.data[0]
            self.assertEqual(len(res_algos), len(algo))
            for i, res_algo in enumerate(res_algos):
                for field in ('description', 'content'):
                    self.assertEqual(res_algo[field]['storageAddress'],
                                     algo[i][field]['storageAddress'])

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
                ledger_algo[field]['storageAddress'] = \
                    ledger_algo[field]['storageAddress'].replace('http://testserver',
                                                                 'http://remotetestserver')
            mquery_ledger.return_value = ledger_algo

            # actual test
            res = self.client.get(url, **self.extra)
            for field in ('description', 'content'):
                self.assertEqual(res.data[field]['storageAddress'],
                                 algo[0][field]['storageAddress'])

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
                ledger_algo[field]['storageAddress'] = \
                    ledger_algo[field]['storageAddress'].replace('http://testserver',
                                                                 'http://remotetestserver')
            mquery_ledger.return_value = ledger_algo

            # actual test
            res = self.client.get(url, **self.extra)
            for field in ('description', 'content'):
                self.assertEqual(res.data[field]['storageAddress'],
                                 algo[0][field]['storageAddress'])

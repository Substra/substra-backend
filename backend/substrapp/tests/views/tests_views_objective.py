import os
import shutil
import logging
import zipfile
import copy
import json

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.serializers import LedgerObjectiveSerializer

from substrapp.ledger.exceptions import LedgerError

from ..common import get_sample_objective, AuthenticatedClient, encode_filter
from ..assets import objective, datamanager, model

MEDIA_ROOT = "/tmp/unittests_views/"
CHANNEL = 'mychannel'


def zip_folder(path, destination):
    zipf = zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for f in files:
            abspath = os.path.join(root, f)
            archive_path = os.path.relpath(abspath, start=path)
            zipf.write(abspath, arcname=archive_path)
    zipf.close()


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(DEFAULT_DOMAIN='https://localhost')
class ObjectiveViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        self.test_data_sample_keys = [
            "2d0f943a-a81a-9cb3-fe84-b162559ce6af",
            "533ee6e7-b9d8-b247-e7e8-53b24547f57e"
        ]

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

    def test_objective_list_empty(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = []

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [])

    def test_objective_list_success(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = objective

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, objective)

    def test_objective_list_filter_fail(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = objective

            search_params = '?search=challenERRORge'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_objective_list_filter_name(self):
        url = reverse('substrapp:objective-list')
        name_to_filter = encode_filter(objective[0]['name'])

        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = objective

            search_params = f'?search=objective%253Aname%253A{name_to_filter}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 1)

    def test_objective_list_filter_metrics(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = objective

            search_params = '?search=objective%253Ametrics%253Atest%2520metrics'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), len(objective))

    def test_objective_list_filter_datamanager(self):
        url = reverse('substrapp:objective-list')

        datamanager_key = objective[0]['test_dataset']['data_manager_key']
        datamanager_to_filter = encode_filter([dm for dm in datamanager
                                               if dm['key'] == datamanager_key].pop()['name'])
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = objective
            mquery_ledger2.return_value = datamanager

            search_params = f'?search=dataset%253Aname%253A{datamanager_to_filter}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 1)

    def test_objective_list_filter_model(self):
        url = reverse('substrapp:objective-list')
        done_model = [
            m for m in model
            if 'traintuple' in m and m['traintuple']['status'] == 'done' and m['testtuple']['objective']
        ][0]
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = objective
            mquery_ledger2.return_value = model

            checksum = done_model['traintuple']['out_model']['hash']
            search_params = f'?search=model%253Ahash%253A{checksum}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 1)

    def test_objective_retrieve(self):
        url = reverse('substrapp:objective-list')

        with mock.patch('substrapp.views.objective.get_object_from_ledger') as mget_object_from_ledger, \
                mock.patch('substrapp.views.objective.get_remote_asset') as get_remote_asset:
            mget_object_from_ledger.return_value = objective[0]

            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../../../../fixtures/owkin/objectives/objective0/description.md'), 'rb') as f:
                content = f.read()

            get_remote_asset.return_value = content

            response = self.client.get(f'{url}{objective[0]["key"]}/', **self.extra)
            r = response.json()

            self.assertEqual(r, objective[0])

    def test_objective_retrieve_fail(self):

        url = reverse('substrapp:objective-list')

        # Key < 32 chars
        search_params = '12312323/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = 'X' * 32 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.objective.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('TEST')

            response = self.client.get(f'{url}{objective[0]["key"]}/', **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_objective_create(self):
        url = reverse('substrapp:objective-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        objective_path = os.path.join(dir_path, '../../../../fixtures/owkin/objectives/objective0/')

        description_path = os.path.join(objective_path, 'description.md')

        metrics_path = os.path.join(MEDIA_ROOT, 'metrics.zip')

        zip_folder(objective_path, metrics_path)

        data = {
            'json': json.dumps({
                'name': 'Simplified skin lesion classification',
                'metrics_name': 'macro-average recall',
                'permissions': {
                    'public': True,
                    'authorized_ids': [],
                },
                'test_data_sample_keys': self.test_data_sample_keys,
                'test_data_manager_key': datamanager[0]['key'],
            }),
            'description': open(description_path, 'rb'),
            'metrics': open(metrics_path, 'rb'),
        }

        with mock.patch.object(LedgerObjectiveSerializer, 'create') as mcreate:

            mcreate.return_value = {}

            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertIsNotNone(response.data['key'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data['description'].close()
        data['metrics'].close()

    def test_objective_leaderboard_sort(self):
        url = reverse('substrapp:objective-leaderboard', args=[objective[0]['key']])
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = {}

            self.client.get(url, data={'sort': 'desc'}, **self.extra)
            mquery_ledger.assert_called_with(
                CHANNEL,
                fcn='queryObjectiveLeaderboard',
                args={
                    'objective_key': objective[0]['key'],
                    'ascendingOrder': False,
                })

            self.client.get(url, data={'sort': 'asc'}, **self.extra)
            mquery_ledger.assert_called_with(
                CHANNEL,
                fcn='queryObjectiveLeaderboard',
                args={
                    'objective_key': objective[0]['key'],
                    'ascendingOrder': True,
                })

        response = self.client.get(url, data={'sort': 'foo'}, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_objective_list_storage_addresses_update(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.objective.get_remote_asset') as mget_remote_asset:

            # mock content
            mget_remote_asset.return_value = b'dummy binary content'
            ledger_objectives = copy.deepcopy(objective)
            for ledger_objective in ledger_objectives:
                for field in ('description', 'metrics'):
                    ledger_objective[field]['storage_address'] = \
                        ledger_objective[field]['storage_address'] \
                        .replace('http://testserver', 'http://remotetestserver')
            mquery_ledger.return_value = ledger_objectives

            # actual test
            res = self.client.get(url, **self.extra)
            res_objectives = res.data
            self.assertEqual(len(res_objectives), len(objective))
            for i, res_objective in enumerate(res_objectives):
                for field in ('description', 'metrics'):
                    self.assertEqual(res_objective[field]['storage_address'],
                                     objective[i][field]['storage_address'])

    def test_objective_retrieve_storage_addresses_update_with_cache(self):
        url = reverse('substrapp:objective-detail', args=[objective[0]['key']])
        with mock.patch('substrapp.views.objective.get_object_from_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.objective.node_has_process_permission',
                           return_value=True), \
                mock.patch('substrapp.views.objective.get_remote_asset') as mget_remote_asset:

            # mock content
            mget_remote_asset.return_value = b'dummy binary content'
            ledger_objective = copy.deepcopy(objective[0])
            for field in ('description', 'metrics'):
                ledger_objective[field]['storage_address'] = \
                    ledger_objective[field]['storage_address'].replace('http://testserver',
                                                                       'http://remotetestserver')
            mquery_ledger.return_value = ledger_objective

            # actual test
            res = self.client.get(url, **self.extra)
            for field in ('description', 'metrics'):
                self.assertEqual(res.data[field]['storage_address'],
                                 objective[0][field]['storage_address'])

    def test_objective_retrieve_storage_addresses_update_without_cache(self):
        url = reverse('substrapp:objective-detail', args=[objective[0]['key']])
        with mock.patch('substrapp.views.objective.get_object_from_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.objective.node_has_process_permission',
                           return_value=False), \
                mock.patch('substrapp.views.objective.get_remote_asset') as mget_remote_asset:

            # mock content
            mget_remote_asset.return_value = b'dummy binary content'
            ledger_objective = copy.deepcopy(objective[0])
            for field in ('description', 'metrics'):
                ledger_objective[field]['storage_address'] = \
                    ledger_objective[field]['storage_address'].replace('http://testserver',
                                                                       'http://remotetestserver')
            mquery_ledger.return_value = ledger_objective

            # actual test
            res = self.client.get(url, **self.extra)
            for field in ('description', 'metrics'):
                self.assertEqual(res.data[field]['storage_address'],
                                 objective[0][field]['storage_address'])

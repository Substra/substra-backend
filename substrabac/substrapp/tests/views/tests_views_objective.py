import os
import shutil
import logging

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase


from substrapp.serializers import LedgerObjectiveSerializer

from substrapp.ledger_utils import LedgerError

from substrapp.views.objective import compute_dryrun as objective_compute_dryrun
from substrapp.utils import compute_hash, get_hash


from ..common import get_sample_objective
from ..common import FakeRequest, FakeTask
from ..assets import objective, datamanager, traintuple, model

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(SITE_HOST='localhost')
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
@override_settings(DEFAULT_DOMAIN='https://localhost')
@override_settings(LEDGER_SYNC_ENABLED=True)
class ObjectiveViewTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        self.test_data_sample_keys = [
            "2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e",
            "533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1"
        ]

        self.extra = {
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
            mquery_ledger.side_effect = [[], ['ISIC']]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

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
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = objective

            search_params = '?search=objective%253Aname%253ASkin%2520Lesion%2520Classification%2520Objective'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_objective_list_filter_metrics(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = objective

            search_params = '?search=objective%253Ametrics%253Amacro-average%2520recall'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), len(objective))

    def test_objective_list_filter_datamanager(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = objective
            mquery_ledger2.return_value = datamanager

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_objective_list_filter_model(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.return_value = objective
            mquery_ledger2.return_value = traintuple

            pkhash = model[1]['traintuple']['outModel']['hash']
            search_params = f'?search=model%253Ahash%253A{pkhash}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_objective_retrieve(self):
        url = reverse('substrapp:objective-list')

        with mock.patch('substrapp.views.objective.get_object_from_ledger') as mget_object_from_ledger, \
                mock.patch('substrapp.views.objective.get_from_node') as mrequestsget:
            mget_object_from_ledger.return_value = objective[0]

            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../../../../fixtures/owkin/objectives/objective0/description.md'), 'rb') as f:
                content = f.read()

            mrequestsget.return_value = FakeRequest(status=status.HTTP_200_OK,
                                                    content=content)

            search_params = f'{compute_hash(content)}/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(r, objective[0])

    def test_objective_retrieve_fail(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        url = reverse('substrapp:objective-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.objective.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('TEST')

            file_hash = get_hash(os.path.join(dir_path,
                                              "../../../../fixtures/owkin/objectives/objective0/description.md"))
            search_params = f'{file_hash}/'
            response = self.client.get(url + search_params, **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_objective_create(self):
        url = reverse('substrapp:objective-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        description_path = os.path.join(dir_path, '../../../../fixtures/owkin/objectives/objective0/description.md')
        metrics_path = os.path.join(dir_path, '../../../../fixtures/owkin/objectives/objective0/metrics.py')

        pkhash = get_hash(description_path)

        test_data_manager_key = get_hash(os.path.join(
            dir_path, '../../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))

        data = {
            'name': 'Simplified skin lesion classification',
            'description': open(description_path, 'rb'),
            'metrics_name': 'macro-average recall',
            'metrics': open(metrics_path, 'rb'),
            'permissions': 'all',
            'test_data_sample_keys': self.test_data_sample_keys,
            'test_data_manager_key': test_data_manager_key
        }

        with mock.patch.object(LedgerObjectiveSerializer, 'create') as mcreate:

            mcreate.return_value = {}

            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data['pkhash'], pkhash)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data['description'].close()
        data['metrics'].close()

    def test_objective_create_dryrun(self):

        url = reverse('substrapp:objective-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        description_path = os.path.join(dir_path, '../../../../fixtures/owkin/objectives/objective0/description.md')
        metrics_path = os.path.join(dir_path, '../../../../fixtures/owkin/objectives/objective0/metrics.py')

        test_data_manager_key = get_hash(os.path.join(
            dir_path, '../../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))

        data = {
            'name': 'Simplified skin lesion classification',
            'description': open(description_path, 'rb'),
            'metrics_name': 'macro-average recall',
            'metrics': open(metrics_path, 'rb'),
            'permissions': 'all',
            'test_data_sample_keys': self.test_data_sample_keys,
            'test_data_manager_key': test_data_manager_key,
            'dryrun': True
        }

        with mock.patch('substrapp.views.objective.compute_dryrun.apply_async') as mdryrun_task:

            mdryrun_task.return_value = FakeTask('42')
            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data['id'], '42')
        self.assertEqual(response.data['message'],
                         'Your dry-run has been taken in account. '
                         'You can follow the task execution on https://localhost/task/42/')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        data['description'].close()
        data['metrics'].close()

    def test_objective_compute_dryrun(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        metrics_path = os.path.join(dir_path, '../../../../fixtures/owkin/objectives/objective0/metrics.py')
        description_path = os.path.join(dir_path, '../../../../fixtures/owkin/objectives/objective0/description.md')
        shutil.copy(metrics_path, os.path.join(MEDIA_ROOT, 'metrics.py'))

        opener_path = os.path.join(dir_path, '../../../../fixtures/owkin/datamanagers/datamanager0/opener.py')

        with open(opener_path, 'rb') as f:
            opener_content = f.read()

        pkhash = get_hash(description_path)

        test_data_manager_key = compute_hash(opener_content)

        with mock.patch('substrapp.views.objective.get_object_from_ledger') as mdatamanager,\
                mock.patch('substrapp.views.objective.get_computed_hash') as mopener:
            mdatamanager.return_value = {'opener': {'storageAddress': 'test'}}
            mopener.return_value = (opener_content, pkhash)
            objective_compute_dryrun(os.path.join(MEDIA_ROOT, 'metrics.py'), test_data_manager_key, pkhash)

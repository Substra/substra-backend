import os
import shutil
import logging

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.views import TrainTupleViewSet, TestTupleViewSet, DataSampleViewSet

from substrapp.serializers import LedgerDataSampleSerializer, LedgerObjectiveSerializer, LedgerAlgoSerializer

from substrapp.utils import JsonException
from substrapp.views.utils import ComputeHashMixin
from substrapp.views.datasample import path_leaf, compute_dryrun as data_sample_compute_dryrun
from substrapp.views.objective import compute_dryrun as objective_compute_dryrun
from substrapp.utils import compute_hash, get_hash
from substrapp.ledger_utils import get_object_from_ledger

from substrapp.models import DataManager

from .common import get_sample_objective, get_sample_datamanager, get_sample_algo, get_sample_model
from .common import FakeAsyncResult, FakeRequest, FakeFilterDataManager, FakeTask, FakeDataManager
from .assets import objective, datamanager, algo, traintuple, model, testtuple

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
class ViewTests(APITestCase):
    def test_data_sample_path_view(self):
        self.assertEqual('tutu', path_leaf('/toto/tata/tutu'))
        self.assertEqual('toto', path_leaf('/toto/'))

    def test_utils_ComputeHashMixin(self):

        compute = ComputeHashMixin()
        myfile = 'toto'
        key = 'tata'

        myfilehash = compute_hash(myfile)
        myfilehashwithkey = compute_hash(myfile, key)

        self.assertEqual(myfilehash, compute.compute_hash(myfile))
        self.assertEqual(myfilehashwithkey, compute.compute_hash(myfile, key))

    def test_utils_get_object_from_ledger(self):

        with mock.patch('substrapp.ledger_utils.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [(objective, status.HTTP_200_OK)]
            data = get_object_from_ledger('', 'queryObjective')

            self.assertEqual(data, objective)

        with mock.patch('substrapp.ledger_utils.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [('', status.HTTP_400_BAD_REQUEST)]
            with self.assertRaises(JsonException):
                get_object_from_ledger('', 'queryAllObjective')


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(DRYRUN_ROOT=MEDIA_ROOT)
@override_settings(SITE_HOST='localhost')
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
@override_settings(DEFAULT_DOMAIN='https://localhost')
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
            mquery_ledger.side_effect = [(None, status.HTTP_200_OK),
                                         (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_objective_list_filter_fail(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [(objective, status.HTTP_200_OK)]

            search_params = '?search=challenERRORge'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_objective_list_filter_name(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [(objective, status.HTTP_200_OK)]

            search_params = '?search=objective%253Aname%253ASkin%2520Lesion%2520Classification%2520Objective'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_objective_list_filter_metrics(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [(objective, status.HTTP_200_OK)]

            search_params = '?search=objective%253Ametrics%253Amacro-average%2520recall'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), len(objective))

    def test_objective_list_filter_datamanager(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.side_effect = [(objective, status.HTTP_200_OK)]
            mquery_ledger2.side_effect = [(datamanager, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_objective_list_filter_model(self):
        url = reverse('substrapp:objective-list')
        with mock.patch('substrapp.views.objective.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.side_effect = [(objective, status.HTTP_200_OK)]
            mquery_ledger2.side_effect = [(traintuple, status.HTTP_200_OK)]

            pkhash = model[0]['traintuple']['outModel']['hash']
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
                                   '../../../fixtures/owkin/objectives/objective0/description.md'), 'rb') as f:
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
            mget_object_from_ledger.side_effect = JsonException('TEST')

            file_hash = get_hash(os.path.join(dir_path, "../../../fixtures/owkin/objectives/objective0/description.md"))
            search_params = f'{file_hash}/'
            response = self.client.get(url + search_params, **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_objective_create(self):
        url = reverse('substrapp:objective-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        description_path = os.path.join(dir_path, '../../../fixtures/owkin/objectives/objective0/description.md')
        metrics_path = os.path.join(dir_path, '../../../fixtures/owkin/objectives/objective0/metrics.py')

        pkhash = get_hash(description_path)

        test_data_manager_key = get_hash(os.path.join(
            dir_path, '../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))

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

            mcreate.return_value = ({},
                                    status.HTTP_201_CREATED)

            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data['pkhash'], pkhash)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data['description'].close()
        data['metrics'].close()

    def test_objective_create_dryrun(self):

        url = reverse('substrapp:objective-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        description_path = os.path.join(dir_path, '../../../fixtures/owkin/objectives/objective0/description.md')
        metrics_path = os.path.join(dir_path, '../../../fixtures/owkin/objectives/objective0/metrics.py')

        test_data_manager_key = get_hash(os.path.join(
            dir_path, '../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))

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

        metrics_path = os.path.join(dir_path, '../../../fixtures/owkin/objectives/objective0/metrics.py')
        description_path = os.path.join(dir_path, '../../../fixtures/owkin/objectives/objective0/description.md')
        shutil.copy(metrics_path, os.path.join(MEDIA_ROOT, 'metrics.py'))

        opener_path = os.path.join(dir_path, '../../../fixtures/owkin/datamanagers/datamanager0/opener.py')

        with open(opener_path, 'rb') as f:
            opener_content = f.read()

        pkhash = get_hash(description_path)

        test_data_manager_key = compute_hash(opener_content)

        with mock.patch('substrapp.views.objective.get_object_from_ledger') as mdatamanager,\
                mock.patch('substrapp.views.objective.get_computed_hash') as mopener:
            mdatamanager.return_value = {'opener': {'storageAddress': 'test'}}
            mopener.return_value = (opener_content, pkhash)
            objective_compute_dryrun(os.path.join(MEDIA_ROOT, 'metrics.py'), test_data_manager_key, pkhash)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(DRYRUN_ROOT=MEDIA_ROOT)
@override_settings(SITE_HOST='localhost')
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class AlgoViewTests(APITestCase):

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
            mquery_ledger.side_effect = [(None, status.HTTP_200_OK),
                                         (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_algo_list_filter_fail(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [(algo, status.HTTP_200_OK)]

            search_params = '?search=algERRORo'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_algo_list_filter_name(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [(algo, status.HTTP_200_OK)]

            search_params = '?search=algo%253Aname%253ALogistic%2520regression'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_algo_list_filter_datamanager_fail(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.side_effect = [(algo, status.HTTP_200_OK)]
            mquery_ledger2.side_effect = [(datamanager, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_algo_list_filter_objective_fail(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.side_effect = [(algo, status.HTTP_200_OK)]
            mquery_ledger2.side_effect = [(objective, status.HTTP_200_OK)]

            search_params = '?search=objective%253Aname%253ASkin%2520Lesion%2520Classification%2520Objective'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_algo_list_filter_model(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.side_effect = [(algo, status.HTTP_200_OK)]
            mquery_ledger2.side_effect = [(traintuple, status.HTTP_200_OK)]

            pkhash = model[0]['traintuple']['outModel']['hash']
            search_params = f'?search=model%253Ahash%253A{pkhash}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_algo_retrieve(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        algo_hash = get_hash(os.path.join(dir_path, '../../../fixtures/chunantes/algos/algo4/algo.tar.gz'))
        url = reverse('substrapp:algo-list')
        algo_response = [a for a in algo if a['key'] == algo_hash][0]
        with mock.patch('substrapp.views.algo.get_object_from_ledger') as mget_object_from_ledger, \
                mock.patch('substrapp.views.algo.get_from_node') as mrequestsget:

            with open(os.path.join(dir_path,
                                   '../../../fixtures/chunantes/algos/algo4/description.md'), 'rb') as f:
                content = f.read()
            mget_object_from_ledger.return_value = algo_response

            mrequestsget.return_value = FakeRequest(status=status.HTTP_200_OK,
                                                    content=content)

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
            mget_object_from_ledger.side_effect = JsonException('TEST')

            file_hash = get_hash(os.path.join(dir_path, "../../../fixtures/owkin/objectives/objective0/description.md"))
            search_params = f'{file_hash}/'
            response = self.client.get(url + search_params, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_algo_create(self):
        url = reverse('substrapp:algo-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        algo_path = os.path.join(dir_path, '../../../fixtures/chunantes/algos/algo3/algo.tar.gz')
        description_path = os.path.join(dir_path, '../../../fixtures/chunantes/algos/algo3/description.md')

        pkhash = get_hash(algo_path)

        data = {'name': 'Logistic regression',
                'file': open(algo_path, 'rb'),
                'description': open(description_path, 'rb'),
                'objective_key': get_hash(os.path.join(
                    dir_path, '../../../fixtures/chunantes/objectives/objective0/description.md')),
                'permissions': 'all'}

        with mock.patch.object(LedgerAlgoSerializer, 'create') as mcreate:

            mcreate.return_value = ({},
                                    status.HTTP_201_CREATED)

            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data['pkhash'], pkhash)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data['description'].close()
        data['file'].close()


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class ModelViewTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.model, self.model_filename = get_sample_model()

        self.extra = {
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
            mquery_ledger.side_effect = [(None, status.HTTP_200_OK),
                                         (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_model_list_filter_fail(self):

        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [(model, status.HTTP_200_OK)]

            url = reverse('substrapp:model-list')
            search_params = '?search=modeERRORl'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertIn('Malformed search filters', r['message'])

    def test_model_list_filter_hash(self):

        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [(model, status.HTTP_200_OK)]

            pkhash = model[0]['traintuple']['outModel']['hash']
            url = reverse('substrapp:model-list')
            search_params = f'?search=model%253Ahash%253A{pkhash}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(len(r[0]), 1)

    def test_model_list_filter_datamanager(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.side_effect = [(model, status.HTTP_200_OK)]
            mquery_ledger2.side_effect = [(datamanager, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253AISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_model_list_filter_objective(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.side_effect = [(model, status.HTTP_200_OK)]
            mquery_ledger2.side_effect = [(objective, status.HTTP_200_OK)]

            search_params = '?search=objective%253Aname%253ASkin%2520Lesion%2520Classification%2520Objective'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_model_list_filter_algo(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.side_effect = [(model, status.HTTP_200_OK)]
            mquery_ledger2.side_effect = [(algo, status.HTTP_200_OK)]

            search_params = '?search=algo%253Aname%253ALogistic%2520regression'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_model_retrieve(self):

        with mock.patch('substrapp.views.model.get_object_from_ledger') as mget_object_from_ledger, \
                mock.patch('substrapp.views.model.get_from_node') as mrequestsget, \
                mock.patch('substrapp.views.model.ModelViewSet.compute_hash') as mcomputed_hash:
            mget_object_from_ledger.return_value = model[0]

            mrequestsget.return_value = FakeRequest(status=status.HTTP_200_OK,
                                                    content=self.model.read().encode())

            mcomputed_hash.return_value = model[0]['traintuple']['outModel']['hash']

            url = reverse('substrapp:model-list')
            search_params = model[0]['traintuple']['outModel']['hash'] + '/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(r, model[0])

    def test_model_retrieve_fail(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        url = reverse('substrapp:model-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.model.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = JsonException('TEST')

            file_hash = get_hash(os.path.join(dir_path, "../../../fixtures/owkin/objectives/objective0/description.md"))
            search_params = f'{file_hash}/'
            response = self.client.get(url + search_params, **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class DataManagerViewTests(APITestCase):

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
            mquery_ledger.side_effect = [(None, status.HTTP_200_OK),
                                         (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_datamanager_list_filter_fail(self):
        url = reverse('substrapp:data_manager-list')
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [(datamanager, status.HTTP_200_OK)]

            search_params = '?search=dataseERRORt'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_datamanager_list_filter_name(self):
        url = reverse('substrapp:data_manager-list')
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = [(datamanager, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_datamanager_list_filter_objective(self):
        url = reverse('substrapp:data_manager-list')
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.side_effect = [(datamanager, status.HTTP_200_OK)]
            mquery_ledger2.side_effect = [(objective, status.HTTP_200_OK)]

            search_params = '?search=objective%253Aname%253ASkin%2520Lesion%2520Classification%2520Objective'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_datamanager_list_filter_model(self):
        url = reverse('substrapp:data_manager-list')
        with mock.patch('substrapp.views.datamanager.query_ledger') as mquery_ledger, \
                mock.patch('substrapp.views.filters_utils.query_ledger') as mquery_ledger2:
            mquery_ledger.side_effect = [(datamanager, status.HTTP_200_OK)]
            mquery_ledger2.side_effect = [(traintuple, status.HTTP_200_OK)]
            pkhash = model[0]['traintuple']['outModel']['hash']
            search_params = f'?search=model%253Ahash%253A{pkhash}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_datamanager_retrieve(self):
        url = reverse('substrapp:data_manager-list')
        datamanager_response = [d for d in datamanager
                                if d['key'] == '615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7'][0]
        with mock.patch('substrapp.views.datamanager.get_object_from_ledger') as mget_object_from_ledger, \
                mock.patch('substrapp.views.datamanager.get_from_node') as mrequestsget:
            mget_object_from_ledger.return_value = datamanager_response

            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'), 'rb') as f:
                opener_content = f.read()

            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../../../fixtures/chunantes/datamanagers/datamanager0/description.md'), 'rb') as f:
                description_content = f.read()

            mrequestsget.side_effect = [FakeRequest(status=status.HTTP_200_OK,
                                                    content=opener_content),
                                        FakeRequest(status=status.HTTP_200_OK,
                                                    content=description_content)]

            search_params = '615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7/'
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
            mget_object_from_ledger.side_effect = JsonException('TEST')

            file_hash = get_hash(os.path.join(dir_path, "../../../fixtures/owkin/objectives/objective0/description.md"))
            search_params = f'{file_hash}/'
            response = self.client.get(url + search_params, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_datamanager_create_dryrun(self):
        url = reverse('substrapp:data_manager-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))
        files = {
            'data_opener': open(
                os.path.join(dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'),
                'rb'),

            'description': open(
                os.path.join(dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/description.md'),
                'rb')}

        data = {
            'name': 'ISIC 2018',
            'type': 'Images',
            'permissions': 'all',
            'dryrun': True
        }

        response = self.client.post(url, {**data, **files}, format='multipart', **self.extra)
        self.assertEqual(response.data, {'message': f'Your data opener is valid. You can remove the dryrun option.'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for x in files:
            files[x].close()


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class TraintupleViewTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        self.logger = logging.getLogger('django.request')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_traintuple_queryset(self):
        traintuple_view = TrainTupleViewSet()
        self.assertFalse(traintuple_view.get_queryset())

    def test_traintuple_list_empty(self):
        url = reverse('substrapp:traintuple-list')
        with mock.patch('substrapp.views.traintuple.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = ([[]], status.HTTP_200_OK)

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

    def test_traintuple_retrieve(self):

        with mock.patch('substrapp.views.traintuple.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.return_value = traintuple[0]
            url = reverse('substrapp:traintuple-list')
            search_params = 'c164f4c714a78c7e2ba2016de231cdd41e3eac61289e08c1f711e74915a0868f/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(r, traintuple[0])

    def test_traintuple_retrieve_fail(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        url = reverse('substrapp:traintuple-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.traintuple.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = JsonException('TEST')

            file_hash = get_hash(os.path.join(dir_path, "../../../fixtures/owkin/objectives/objective0/description.md"))
            search_params = f'{file_hash}/'
            response = self.client.get(url + search_params, **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class TesttupleViewTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        self.logger = logging.getLogger('django.request')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_testtuple_queryset(self):
        testtuple_view = TestTupleViewSet()
        self.assertFalse(testtuple_view.get_queryset())

    def test_testtuple_list_empty(self):
        url = reverse('substrapp:testtuple-list')
        with mock.patch('substrapp.views.testtuple.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = ([[]], status.HTTP_200_OK)

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

    def test_testtuple_retrieve(self):

        with mock.patch('substrapp.views.testtuple.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.return_value = testtuple[0]
            url = reverse('substrapp:testtuple-list')
            search_params = 'c164f4c714a78c7e2ba2016de231cdd41e3eac61289e08c1f711e74915a0868f/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(r, testtuple[0])

    def test_testtuple_retrieve_fail(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        url = reverse('substrapp:testtuple-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.testtuple.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = JsonException('TEST')

            file_hash = get_hash(os.path.join(dir_path, "../../../fixtures/owkin/objectives/objective0/description.md"))
            search_params = f'{file_hash}/'
            response = self.client.get(url + search_params, **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class TaskViewTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        self.logger = logging.getLogger('django.request')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_task_retrieve(self):

        url = reverse('substrapp:task-detail', kwargs={'pk': 'pk'})
        with mock.patch('substrapp.views.task.AsyncResult') as mAsyncResult:
            mAsyncResult.return_value = FakeAsyncResult(status='SUCCESS')
            response = self.client.get(url, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_task_retrieve_fail(self):
        url = reverse('substrapp:task-detail', kwargs={'pk': 'pk'})
        with mock.patch('substrapp.views.task.AsyncResult') as mAsyncResult:
            mAsyncResult.return_value = FakeAsyncResult()
            response = self.client.get(url, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_task_retrieve_pending(self):
        url = reverse('substrapp:task-detail', kwargs={'pk': 'pk'})
        with mock.patch('substrapp.views.task.AsyncResult') as mAsyncResult:
            mAsyncResult.return_value = FakeAsyncResult(status='PENDING', successful=False)
            response = self.client.get(url, **self.extra)
            self.assertEqual(response.data['message'],
                             'Task is either waiting, does not exist in this context or has been removed after 24h')

            self.assertEqual(response.status_code, status.HTTP_200_OK)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(DRYRUN_ROOT=MEDIA_ROOT)
@override_settings(SITE_HOST='localhost')
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
@override_settings(DEFAULT_DOMAIN='https://localhost')
class DataViewTests(APITestCase):

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

    def test_data_create_bulk(self):
        url = reverse('substrapp:data_sample-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')
        data_path2 = os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/datasample0/0024899.zip')

        # dir hash
        pkhash1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'
        pkhash2 = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))]

        data = {
            'files': [path_leaf(data_path1), path_leaf(data_path2)],
            path_leaf(data_path1): open(data_path1, 'rb'),
            path_leaf(data_path2): open(data_path2, 'rb'),
            'data_manager_keys': data_manager_keys,
            'test_only': False
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mcreate.return_value = ({'keys': [pkhash1, pkhash2]},
                                    status.HTTP_201_CREATED)
            response = self.client.post(url, data=data, format='multipart', **self.extra)
        self.assertEqual([r['pkhash'] for r in response.data], [pkhash1, pkhash2])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for x in data['files']:
            data[x].close()

    def test_data_create_bulk_dryrun(self):
        url = reverse('substrapp:data_sample-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')
        data_path2 = os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/datasample0/0024899.zip')

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))]

        data = {
            'files': [path_leaf(data_path1), path_leaf(data_path2)],
            path_leaf(data_path1): open(data_path1, 'rb'),
            path_leaf(data_path2): open(data_path2, 'rb'),
            'data_manager_keys': data_manager_keys,
            'test_only': False,
            'dryrun': True
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(DataSampleViewSet, 'dryrun_task') as mdryrun_task:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mdryrun_task.return_value = (
                FakeTask('42'),
                'Your dry-run has been taken in account. You can follow the task execution on localhost')
            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data['id'], '42')
        self.assertEqual(response.data['message'],
                         'Your dry-run has been taken in account. You can follow the task execution on localhost')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        for x in data['files']:
            data[x].close()

    def test_data_create(self):
        url = reverse('substrapp:data_sample-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path = os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')

        # dir hash
        pkhash = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))]

        data = {
            'file': open(data_path, 'rb'),
            'data_manager_keys': data_manager_keys,
            'test_only': False
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mcreate.return_value = ({'keys': [pkhash]},
                                    status.HTTP_201_CREATED)
            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data[0]['pkhash'], pkhash)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data['file'].close()

    def test_data_create_dryrun(self):

        url = reverse('substrapp:data_sample-list')

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path = os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))]

        data = {
            'file': open(data_path, 'rb'),
            'data_manager_keys': data_manager_keys,
            'test_only': False,
            'dryrun': True
        }

        with mock.patch.object(DataManager.objects, 'filter') as mdatamanager, \
                mock.patch.object(DataSampleViewSet, 'dryrun_task') as mdryrun_task:

            mdatamanager.return_value = FakeFilterDataManager(1)
            mdryrun_task.return_value = (
                FakeTask('42'),
                'Your dry-run has been taken in account. You can follow the task execution on localhost')
            response = self.client.post(url, data=data, format='multipart', **self.extra)

        self.assertEqual(response.data['id'], '42')
        self.assertEqual(response.data['message'],
                         'Your dry-run has been taken in account. You can follow the task execution on localhost')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        data['file'].close()

    def test_data_sample_compute_dryrun(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path = os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip')

        shutil.copy(data_path, os.path.join(MEDIA_ROOT, '0024700.zip'))

        opener_path = os.path.join(dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/opener.py')

        pkhash = get_hash(data_path)

        data = {
            'filepath': os.path.join(MEDIA_ROOT, '0024700.zip'),
            'pkhash': pkhash,
        }

        data_files = [data]
        data_manager_keys = [get_hash(opener_path)]

        with mock.patch.object(DataManager.objects, 'get') as mdatamanager:
            mdatamanager.return_value = FakeDataManager(opener_path)
            data_sample_compute_dryrun(data_files, data_manager_keys)

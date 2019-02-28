import os
import shutil
import tempfile

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.views import DatasetViewSet, TrainTupleViewSet, ChallengeViewSet, AlgoViewSet, ModelViewSet
from substrapp.views.utils import JsonException, ComputeHashMixin
from substrapp.views.data import path_leaf
from substrapp.utils import compute_hash

from substrapp.models import Challenge, Dataset, Algo, Model

from .common import get_sample_challenge, get_sample_dataset, get_sample_data, get_sample_script, get_sample_algo, get_sample_model
from .assets import challenge, data, dataset, algo, traintuple, testtuple, model

MEDIA_ROOT = tempfile.mkdtemp()


# APITestCase
class ViewTests(APITestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_traintuple_queryset(self):
        traintuple_view = TrainTupleViewSet()
        self.assertFalse(traintuple_view.get_queryset())

    def test_data_path_view(self):
        self.assertEqual('tutu', path_leaf('/toto/tata/tutu'))
        self.assertEqual('toto', path_leaf('/toto/'))

    def test_utils_ComputeHashMixin(self):

        compute = ComputeHashMixin()
        myfile = 'toto'
        myfilehash = compute_hash(myfile)

        self.assertEqual(myfilehash, compute.compute_hash(myfile))


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'org': {'org_name': 'test-org'}, 'peer': 'test-peer'})
class ChallengeViewTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.challenge_description, self.challenge_description_filename, \
            self.challenge_metrics, self.challenge_metrics_filename = get_sample_challenge()

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_challenge_list_empty(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(None, status.HTTP_200_OK),
                                        (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_challenge_list_filter_fail(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK)]

            search_params = '?search=challenERRORge'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_challenge_list_filter_name(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK)]

            search_params = '?search=challenge%253Aname%253ASkin%2520Lesion%2520Classification%2520Challenge'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_challenge_list_filter_metrics(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK)]

            search_params = '?search=challenge%253Ametrics%253Amacro-average%2520recall'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_challenge_list_filter_dataset(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK),
                                        (dataset, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_challenge_list_filter_algo(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK),
                                        (algo, status.HTTP_200_OK)]

            url = reverse('substrapp:challenge-list')
            search_params = '?search=algo%253Aname%253ALogistic%2520regression'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_challenge_list_filter_model(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK),
                                        (traintuple, status.HTTP_200_OK)]

            search_params = '?search=model%253Ahash%253A454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_challenge_retrieve(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.getObjectFromLedger') as mgetObjectFromLedger, \
                mock.patch.object(ChallengeViewSet, 'create_or_update_challenge') as mcreate_or_update_challenge:
            mgetObjectFromLedger.return_value = challenge[0]
            mcreate_or_update_challenge.return_value = Challenge.objects.create(description=self.challenge_description,
                                                                                metrics=self.challenge_metrics)

            search_params = '6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(r, challenge[0])

    def test_challenge_retrieve_fail(self):
        url = reverse('substrapp:challenge-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.challenge.getObjectFromLedger') as mgetObjectFromLedger:
            mgetObjectFromLedger.side_effect = JsonException('TEST')

            search_params = '6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/'
            response = self.client.get(url + search_params, **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'org': {'org_name': 'test-org'}, 'peer': 'test-peer'})
class AlgoViewTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.algo, self.algo_filename = get_sample_algo()

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_algo_list_empty(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(None, status.HTTP_200_OK),
                                        (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_algo_list_filter_fail(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(algo, status.HTTP_200_OK)]

            search_params = '?search=algERRORo'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_algo_list_filter_name(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(algo, status.HTTP_200_OK)]

            search_params = '?search=algo%253Aname%253ALogistic%2520regression'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_algo_list_filter_dataset(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(algo, status.HTTP_200_OK),
                                        (dataset, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_algo_list_filter_challenge(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(algo, status.HTTP_200_OK),
                                        (challenge, status.HTTP_200_OK)]

            search_params = '?search=challenge%253Aname%253ASkin%2520Lesion%2520Classification%2520Challenge'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 3)

    def test_algo_list_filter_model(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(algo, status.HTTP_200_OK),
                                        (traintuple, status.HTTP_200_OK)]

            search_params = '?search=model%253Ahash%253A454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_algo_retrieve(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.getObjectFromLedger') as mgetObjectFromLedger, \
                mock.patch.object(AlgoViewSet, 'create_or_update_algo') as mcreate_or_update_algo:
            mgetObjectFromLedger.return_value = algo[3]
            mcreate_or_update_algo.return_value = Algo.objects.create(file=self.algo)

            search_params = 'f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(r, algo[3])

    def test_algo_retrieve_fail(self):
        url = reverse('substrapp:algo-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.algo.getObjectFromLedger') as mgetObjectFromLedger:
            mgetObjectFromLedger.side_effect = JsonException('TEST')

            search_params = '6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/'
            response = self.client.get(url + search_params, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'org': {'org_name': 'test-org'}, 'peer': 'test-peer'})
class ModelViewTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.model, self.model_filename = get_sample_model()

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_model_list_empty(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(None, status.HTTP_200_OK),
                                        (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_model_list_filter_fail(self):

        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(model, status.HTTP_200_OK)]

            url = reverse('substrapp:model-list')
            search_params = '?search=modeERRORl'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertIn('Malformed search filters', r['message'])

    def test_model_list_filter_hash(self):

        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(model, status.HTTP_200_OK)]

            url = reverse('substrapp:model-list')
            search_params = '?search=model%253Ahash%253A454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_model_list_filter_dataset(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(model, status.HTTP_200_OK),
                                        (dataset, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253AISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_model_list_filter_challenge(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(model, status.HTTP_200_OK),
                                        (challenge, status.HTTP_200_OK)]

            search_params = '?search=challenge%253Aname%253ASimplified%2520skin%2520lesion%2520classification'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_model_list_filter_algo(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(model, status.HTTP_200_OK),
                                        (algo, status.HTTP_200_OK)]

            search_params = '?search=algo%253Aname%253ALogistic%2520regression'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_model_retrieve(self):

        with mock.patch('substrapp.views.model.getObjectFromLedger') as mgetObjectFromLedger, \
                mock.patch.object(ModelViewSet, 'create_or_update_model') as mcreate_or_update_model:
            mgetObjectFromLedger.return_value = model[0]
            instance = Model.objects.create(pkhash=model[0]['traintuple']['outModel']['hash'], validated=True, file=self.model)
            mcreate_or_update_model.return_value = instance

            url = reverse('substrapp:model-list')
            search_params = '454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(r, model[0])

    def test_model_retrieve_fail(self):
        url = reverse('substrapp:model-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.model.getObjectFromLedger') as mgetObjectFromLedger:
            mgetObjectFromLedger.side_effect = JsonException('TEST')

            search_params = '6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/'
            response = self.client.get(url + search_params, **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'org': {'org_name': 'test-org'}, 'peer': 'test-peer'})
class DatasetViewTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.data_description, self.data_description_filename, \
            self.data_data_opener, self.data_opener_filename = get_sample_dataset()

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_dataset_list_empty(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(None, status.HTTP_200_OK),
                                        (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_dataset_list_filter_fail(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(dataset, status.HTTP_200_OK)]

            search_params = '?search=dataseERRORt'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_dataset_list_filter_name(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(dataset, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_dataset_list_filter_algo(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(dataset, status.HTTP_200_OK),
                                        (algo, status.HTTP_200_OK)]

            search_params = '?search=algo%253Aname%253ALogistic%2520regression%2520for%2520balanced%2520problem'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_dataset_list_filter_challenge(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(dataset, status.HTTP_200_OK),
                                        (challenge, status.HTTP_200_OK)]

            search_params = '?search=challenge%253Aname%253ASimplified%2520skin%2520lesion%2520classification'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_dataset_list_filter_model(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(dataset, status.HTTP_200_OK),
                                        (traintuple, status.HTTP_200_OK)]

            search_params = '?search=model%253Ahash%253A454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_dataset_retrieve(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch.object(DatasetViewSet, 'getObjectFromLedger') as mgetObjectFromLedger, \
                mock.patch.object(DatasetViewSet, 'create_or_update_dataset') as mcreate_or_update_dataset:
            mgetObjectFromLedger.return_value = dataset[1]
            mcreate_or_update_dataset.return_value = Dataset.objects.create(name='slide',
                                                                            description=self.data_description,
                                                                            data_opener=self.data_data_opener)

            search_params = '6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(r, dataset[1])

    def test_dataset_retrieve_fail(self):
        url = reverse('substrapp:dataset-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch.object(DatasetViewSet, 'getObjectFromLedger') as mgetObjectFromLedger:
            mgetObjectFromLedger.side_effect = JsonException('TEST')

            search_params = '6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/'
            response = self.client.get(url + search_params, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

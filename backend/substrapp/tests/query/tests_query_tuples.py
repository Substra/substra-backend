import os
import shutil
import tempfile

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.models import Objective
from substrapp.utils import new_uuid

from ..common import get_sample_objective, AuthenticatedClient

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TraintupleQueryTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        self.train_data_sample_keys = ['5c1d9cd1-c2c1-082d-de09-21b56d11030c']
        self.fake_key = '5c1d9cd1-c2c1-082d-de09-21b56d11030c'

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_add_traintuple_sync_ok(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:traintuple-list')

        data = {
            'train_data_sample_keys': self.train_data_sample_keys,
            'algo_key': self.fake_key,
            'data_manager_key': self.fake_key,
            'objective_key': self.fake_key,
            'compute_plan_id': self.fake_key,
            'in_models_keys': [self.fake_key]}
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.assets.invoke_ledger') as minvoke_ledger, \
                mock.patch('substrapp.views.traintuple.query_ledger') as mquery_ledger:

            key = new_uuid()
            mquery_ledger.return_value = {'key': key}
            minvoke_ledger.return_value = {'pkhash': key}

            response = self.client.post(url, data, format='json', **extra)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_traintuple_with_implicit_compute_plan(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:traintuple-list')

        data = {
            'train_data_sample_keys': self.train_data_sample_keys,
            'algo_key': self.fake_key,
            'data_manager_key': self.fake_key,
            'objective_key': self.fake_key,
            'in_models_keys': [self.fake_key],
            # implicit compute plan
            'rank': 0,
            'compute_plan_id': None
        }
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.assets.create_computeplan') as mcreate_computeplan, \
                mock.patch('substrapp.ledger.assets.create_traintuple') as mcreate_traintuple:

            mcreate_computeplan.return_value = {'compute_plan_id': str(new_uuid())}
            mcreate_traintuple.return_value = {'key': str(new_uuid())}

            response = self.client.post(url, data, format='json', **extra)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(mcreate_computeplan.call_count, 1)
            self.assertEqual(mcreate_traintuple.call_count, 1)

    @override_settings(LEDGER_SYNC_ENABLED=False)
    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory'
    )
    def test_add_traintuple_no_sync_ok(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:traintuple-list')

        data = {
            'train_data_sample_keys': self.train_data_sample_keys,
            'algo_key': self.fake_key,
            'data_manager_key': self.fake_key,
            'objective_key': self.fake_key,
            'compute_plan_id': self.fake_key,
            'in_models_keys': [self.fake_key]}
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.assets.invoke_ledger') as minvoke_ledger, \
                mock.patch('substrapp.views.traintuple.query_ledger') as mquery_ledger:

            key = new_uuid()
            mquery_ledger.return_value = {'key': key}
            minvoke_ledger.return_value = None

            response = self.client.post(url, data, format='json', **extra)

            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_traintuple_ko(self):
        url = reverse('substrapp:traintuple-list')

        data = {
            'train_data_sample_keys': self.train_data_sample_keys,
            'model_key': self.fake_key
        }

        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        response = self.client.post(url, data, format='json', **extra)
        r = response.json()
        self.assertIn('This field may not be null.', r['algo_key'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        o = Objective.objects.create(description=self.objective_description,
                                     metrics=self.objective_metrics)
        data = {'objective': o.pkhash}
        response = self.client.post(url, data, format='json', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TesttupleQueryTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()
        self.objective_key = '5c1d9cd1-c2c1-082d-de09-21b56d11030c'
        self.test_data_sample_keys = ['5c1d9cd1-c2c1-082d-de09-21b56d11030c']
        self.fake_key = '5c1d9cd1-c2c1-082d-de09-21b56d11030c'

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_add_testtuple_sync_ok(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:testtuple-list')

        data = {
            'objective_key': self.objective_key,
            'test_data_sample_keys': self.test_data_sample_keys,
            'traintuple_key': self.fake_key,
            'data_manager_key': self.fake_key}
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.assets.invoke_ledger') as minvoke_ledger, \
                mock.patch('substrapp.views.testtuple.query_ledger') as mquery_ledger:

            key = new_uuid()
            mquery_ledger.return_value = {'key': key}
            minvoke_ledger.return_value = {'pkhash': key}

            response = self.client.post(url, data, format='json', **extra)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(LEDGER_SYNC_ENABLED=False)
    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory'
    )
    def test_add_testtuple_no_sync_ok(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:testtuple-list')

        data = {
            'objective_key': self.objective_key,
            'test_data_sample_keys': self.test_data_sample_keys,
            'traintuple_key': self.fake_key,
            'data_manager_key': self.fake_key}
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.assets.invoke_ledger') as minvoke_ledger, \
                mock.patch('substrapp.views.testtuple.query_ledger') as mquery_ledger:

            key = new_uuid()
            mquery_ledger.return_value = {'key': key}
            minvoke_ledger.return_value = None

            response = self.client.post(url, data, format='json', **extra)

            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_testtuple_ko(self):
        url = reverse('substrapp:testtuple-list')

        data = {
            'test_data_sample_keys': self.test_data_sample_keys,
        }

        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        response = self.client.post(url, data, format='json', **extra)
        r = response.json()
        self.assertIn('This field may not be null.', r['traintuple_key'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

import os
import shutil
import mock
import uuid

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.ledger.exceptions import LedgerError
from substrapp.serializers import LedgerComputePlanSerializer

from ..common import AuthenticatedClient
from ..assets import computeplan

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ComputePlanViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_create(self):
        url = reverse('substrapp:compute_plan-list')

        dummy_key = str(uuid.uuid4())

        data = {
            'traintuples': [{
                'algo_key': dummy_key,
                'data_manager_key': dummy_key,
                'train_data_sample_keys': [dummy_key],
                'traintuple_id': dummy_key,
            }],
            'testtuples': [{
                'traintuple_id': dummy_key,
                'objective_key': dummy_key,
                'data_manager_key': dummy_key,
            }]
        }

        with mock.patch.object(LedgerComputePlanSerializer, 'create') as mcreate:
            with mock.patch('substrapp.views.computeplan.query_ledger') as mquery:
                mcreate.return_value = {}
                mquery.return_value = {}

                response = self.client.post(url, data=data, format='json', **self.extra)

        self.assertEqual(response.json(), {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_computeplan_list_empty(self):
        url = reverse('substrapp:compute_plan-list')
        with mock.patch('substrapp.views.computeplan.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = []

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [])

    def test_computeplan_list_success(self):
        url = reverse('substrapp:compute_plan-list')
        with mock.patch('substrapp.views.computeplan.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = computeplan

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, computeplan)

    def test_computeplan_retrieve(self):
        with mock.patch('substrapp.views.computeplan.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.return_value = computeplan[0]

            url = reverse('substrapp:compute_plan-detail', args=[computeplan[0]['compute_plan_id']])
            response = self.client.get(url, **self.extra)
            r = response.json()

            self.assertEqual(r, computeplan[0])

    def test_computeplan_retrieve_fail(self):
        url = reverse('substrapp:compute_plan-list')

        # Key < 32 chars
        search_params = '12312323/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = 'X' * 32 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.computeplan.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('TEST')

            search_params = computeplan[0]['compute_plan_id']
            response = self.client.get(url + search_params + '/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_computeplan_cancel(self):
        cp = computeplan[0]
        key = cp['compute_plan_id']
        with mock.patch('substrapp.views.computeplan.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = cp

            url = reverse('substrapp:compute_plan-cancel', args=[key])
            response = self.client.post(url, **self.extra)
            r = response.json()
            self.assertEqual(r, cp)

    def test_computeplan_update(self):
        cp = computeplan[0]
        compute_plan_id = cp['compute_plan_id']
        url = reverse('substrapp:compute_plan-update-ledger', args=[compute_plan_id])

        with mock.patch('substrapp.ledger.assets.update_computeplan', return_value=cp):
            response = self.client.post(url, **self.extra)
            r = response.json()
            self.assertEqual(r, cp)

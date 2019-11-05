import os
import shutil

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.serializers import LedgerComputePlanSerializer
from ..common import AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
@override_settings(LEDGER_SYNC_ENABLED=True)
class ComputePlanViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_create(self):
        url = reverse('substrapp:compute_plan-list')

        dummy_key = 'x' * 64

        data = {
            'algo_key': dummy_key,
            'objective_key': dummy_key,
            'traintuples': [{
                'data_manager_key': dummy_key,
                'train_data_sample_keys': [dummy_key],
                'traintuple_id': dummy_key,
            }],
            'testtuples': [{
                'traintuple_id': dummy_key,
                'data_manager_key': dummy_key,
            }],
        }

        with mock.patch.object(LedgerComputePlanSerializer, 'create') as mcreate:
            with mock.patch('substrapp.views.computeplan.query_ledger') as mquery:
                mcreate.return_value = {}
                mquery.return_value = {}

                response = self.client.post(url, data=data, format='json', **self.extra)

        self.assertEqual(response.json(), {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

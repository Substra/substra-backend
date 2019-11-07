import os
import shutil
import logging

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.views import CompositeTraintupleViewSet

from substrapp.utils import get_hash

from substrapp.ledger_utils import LedgerError

from ..assets import compositetraintuple
from ..common import AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


def get_compute_plan_id(assets):
    for asset in assets:
        compute_plan_id = asset.get('computePlanID')
        if compute_plan_id:
            return compute_plan_id
    raise Exception('Could not find a compute plan ID')


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class CompositeTraintupleViewTests(APITestCase):
    client_class = AuthenticatedClient

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

    def test_compositetraintuple_queryset(self):
        compositetraintuple_view = CompositeTraintupleViewSet()
        self.assertFalse(compositetraintuple_view.get_queryset())

    def test_compositetraintuple_list_empty(self):
        url = reverse('substrapp:composite_traintuple-list')
        with mock.patch('substrapp.views.compositetraintuple.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = []

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

    def test_compositetraintuple_retrieve(self):

        with mock.patch('substrapp.views.compositetraintuple.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.return_value = compositetraintuple[0]
            url = reverse('substrapp:composite_traintuple-list')
            search_params = 'c164f4c714a78c7e2ba2016de231cdd41e3eac61289e08c1f711e74915a0868f/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(r, compositetraintuple[0])

    def test_compositetraintuple_retrieve_fail(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        url = reverse('substrapp:composite_traintuple-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.compositetraintuple.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('Test')

            file_hash = get_hash(os.path.join(dir_path,
                                              "../../../../fixtures/owkin/objectives/objective0/description.md"))
            search_params = f'{file_hash}/'
            response = self.client.get(url + search_params, **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compositetraintuple_list_filter_tag(self):
        url = reverse('substrapp:composite_traintuple-list')
        with mock.patch('substrapp.views.compositetraintuple.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = compositetraintuple

            search_params = '?search=composite_traintuple%253Atag%253Asubstra'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_compositetraintuple_list_filter_compute_plan_id(self):
        url = reverse('substrapp:composite_traintuple-list')
        with mock.patch('substrapp.views.compositetraintuple.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = compositetraintuple
            compute_plan_id = get_compute_plan_id(compositetraintuple)
            search_params = f'?search=composite_traintuple%253AcomputePlanID%253A{compute_plan_id}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

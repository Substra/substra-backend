import os
import shutil
import logging
import urllib

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.views import TrainTupleViewSet, TestTupleViewSet

from substrapp.ledger.exceptions import LedgerError

from ..assets import traintuple, testtuple, objective
from ..common import AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


def get_compute_plan_id(assets):
    for asset in assets:
        compute_plan_id = asset.get('compute_plan_id')
        if compute_plan_id:
            return compute_plan_id
    raise Exception('Could not find a compute plan ID')


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TraintupleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

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

    def test_traintuple_queryset(self):
        traintuple_view = TrainTupleViewSet()
        self.assertFalse(traintuple_view.get_queryset())

    def test_traintuple_list_empty(self):
        url = reverse('substrapp:traintuple-list')
        with mock.patch('substrapp.views.traintuple.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = []

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [])

    def test_traintuple_retrieve(self):

        with mock.patch('substrapp.views.traintuple.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.return_value = traintuple[0]
            url = reverse('substrapp:traintuple-list')
            search_params = 'c164f4c7-14a7-8c7e-2ba2-016de231cdd4/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(r, traintuple[0])

    def test_traintuple_retrieve_fail(self):

        url = reverse('substrapp:traintuple-list')

        # PKhash < 32 chars
        search_params = '12312323/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PKhash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.traintuple.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('Test')

            response = self.client.get(f'{url}{objective[0]["key"]}/', **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_traintuple_list_filter_tag(self):
        url = reverse('substrapp:traintuple-list')
        with mock.patch('substrapp.views.traintuple.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = traintuple
            target_tag = 'foo'
            search_params = '?search=traintuple%253Atag%253A' + urllib.parse.quote_plus(target_tag)
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 2)

    def test_traintuple_list_filter_compute_plan_id(self):
        url = reverse('substrapp:traintuple-list')
        with mock.patch('substrapp.views.traintuple.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = traintuple
            compute_plan_id = get_compute_plan_id(traintuple)
            search_params = f'?search=traintuple%253Acompute_plan_id%253A{compute_plan_id}'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 2)


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TesttupleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

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

    def test_testtuple_queryset(self):
        testtuple_view = TestTupleViewSet()
        self.assertFalse(testtuple_view.get_queryset())

    def test_testtuple_list_empty(self):
        url = reverse('substrapp:testtuple-list')
        with mock.patch('substrapp.views.testtuple.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = []

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [])

    def test_testtuple_retrieve(self):

        with mock.patch('substrapp.views.testtuple.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.return_value = testtuple[0]
            url = reverse('substrapp:testtuple-list')
            search_params = 'c164f4c7-14a7-8c7e-2ba2-016de231cdd4/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(r, testtuple[0])

    def test_testtuple_retrieve_fail(self):

        url = reverse('substrapp:testtuple-list')

        # PKhash < 32 chars
        search_params = '12312323/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PKhash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.testtuple.get_object_from_ledger') as mget_object_from_ledger:
            mget_object_from_ledger.side_effect = LedgerError('Test')
            response = self.client.get(f'{url}{objective[0]["key"]}/', **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_testtuple_list_filter_tag(self):
        url = reverse('substrapp:testtuple-list')
        with mock.patch('substrapp.views.testtuple.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = testtuple

            search_params = '?search=testtuple%253Atag%253Abar'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 1)

            search_params = '?search=testtuple%253Atag%253Afoo'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r), 0)

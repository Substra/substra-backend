import os
import logging
import shutil

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework.test import APITestCase

from ..common import AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class ModelViewTests(APITestCase):
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

    def test_node_list_success(self):
        url = reverse('substrapp:node-list')
        with mock.patch('substrapp.views.node.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = {'node_ids': ['foo', 'bar']}
            with mock.patch('substrapp.views.node.get_owner') as mget_owner:
                mget_owner.return_value = 'foo'

                response = self.client.get(url, **self.extra)
                r = response.json()
                self.assertEqual(r, [
                    {'nodeID': 'foo', 'isCurrent': True},
                    {'nodeID': 'bar', 'isCurrent': False}
                ])

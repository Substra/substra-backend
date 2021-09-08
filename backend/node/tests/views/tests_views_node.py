import os
import logging

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework.test import APITestCase

from substrapp.tests.common import AuthenticatedClient
from substrapp.orchestrator.api import OrchestratorClient

MEDIA_ROOT = "/tmp/unittests_views/"


@override_settings(MEDIA_ROOT=MEDIA_ROOT,
                   LEDGER_CHANNELS={'mychannel': {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}})
class ModelViewTests(APITestCase):
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
        self.logger.setLevel(self.previous_level)

    def test_node_list_success(self):
        url = reverse('node:node-list')
        with mock.patch.object(OrchestratorClient, 'query_nodes', return_value=[{'id': 'foo'}, {'id': 'bar'}]), \
                mock.patch('node.views.node.get_owner', return_value='foo'):
            response = self.client.get(url, **self.extra)
            self.assertEqual(response.json(), [
                {'id': 'foo', 'is_current': True},
                {'id': 'bar', 'is_current': False}
            ])

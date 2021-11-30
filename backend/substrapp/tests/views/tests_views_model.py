import copy
import logging
import os
import shutil

import mock
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from grpc import RpcError
from grpc import StatusCode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from node.authentication import NodeUser
from orchestrator.client import OrchestratorClient
from substrapp.views.model import ModelPermissionViewSet
from substrapp.views.utils import AssetPermissionError

from .. import assets
from ..common import AuthenticatedClient
from ..common import get_sample_model

MEDIA_ROOT = "/tmp/unittests_views/"
CHANNEL = "mychannel"
TEST_ORG = "MyTestOrg"
MODEL_KEY = "some-key"


# APITestCase
@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    LEDGER_MSP_ID=TEST_ORG,
)
class ModelViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.model, self.model_filename = get_sample_model()

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": CHANNEL, "HTTP_ACCEPT": "application/json;version=0.0"}

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

        self.maxDiff = None

        self.url = reverse("substrapp:model-list")

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_model_list_empty(self):
        with mock.patch.object(OrchestratorClient, "query_models", return_value=[]):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r, {"count": 0, "next": None, "previous": None, "results": []})

    def test_model_list_filter_fail(self):
        models = assets.get_models()
        with mock.patch.object(OrchestratorClient, "query_models", return_value=models):
            search_params = "?search=modeERRORl"
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()
            self.assertIn("Malformed search filters", r["message"])

    def test_model_list_filter_key(self):
        models = assets.get_models()
        o_models = copy.deepcopy(models)
        with mock.patch.object(OrchestratorClient, "query_models", return_value=o_models):
            key = models[1]["key"]
            search_params = f"?search=model%253Akey%253A{key}"
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(len(r["results"]), 1)

    def test_model_retrieve(self):
        model = assets.get_model()
        expected = copy.deepcopy(model)
        with mock.patch.object(OrchestratorClient, "query_model", return_value=model):
            url = reverse("substrapp:model-list")
            search_params = model["key"] + "/"
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(r, expected)

    def test_model_retrieve_fail(self):
        # Key < 32 chars
        search_params = "12312323/"
        response = self.client.get(self.url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = "X" * 32 + "/"
        response = self.client.get(self.url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = RpcError()
        error.details = "out of range test"
        error.code = lambda: StatusCode.OUT_OF_RANGE

        metric = assets.get_metric()

        with mock.patch.object(OrchestratorClient, "query_model", side_effect=error):
            response = self.client.get(f'{self.url}{metric["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_model_download_by_node_for_worker(self):
        """ "Simple node-to-node download, e.g. worker downloads in-model"""
        pvs = ModelPermissionViewSet()

        pvs.check_access(
            CHANNEL,
            NodeUser(),
            {"key": MODEL_KEY, "permissions": {"process": {"public": True}}},
            is_proxied_request=False,
        )

        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                NodeUser(),
                {"key": MODEL_KEY, "permissions": {"process": {"public": False, "authorized_ids": []}}},
                is_proxied_request=False,
            )

        pvs.check_access(
            CHANNEL,
            NodeUser(username="foo"),
            {"key": MODEL_KEY, "permissions": {"process": {"public": False, "authorized_ids": ["foo"]}}},
            is_proxied_request=False,
        )

    @override_settings(LEDGER_CHANNELS={CHANNEL: {"model_export_enabled": True}})
    def test_model_export_proxied(self):
        """Model export (proxied) with option enabled"""
        pvs = ModelPermissionViewSet()

        pvs.check_access(
            CHANNEL,
            NodeUser(),
            {"key": MODEL_KEY, "permissions": {"download": {"public": True}}},
            is_proxied_request=True,
        )

        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                NodeUser(),
                {"key": MODEL_KEY, "permissions": {"download": {"public": False, "authorized_ids": []}}},
                is_proxied_request=True,
            )

        pvs.check_access(
            CHANNEL,
            NodeUser(username="foo"),
            {"key": MODEL_KEY, "permissions": {"download": {"public": False, "authorized_ids": ["foo"]}}},
            is_proxied_request=True,
        )

    @override_settings(LEDGER_CHANNELS={CHANNEL: {"model_export_enabled": False}})
    def test_model_download_by_node_proxied_option_disabled(self):
        """Model export (proxied) with option disabled"""
        pvs = ModelPermissionViewSet()

        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                NodeUser(),
                {"key": MODEL_KEY, "permissions": {"download": {"public": True}}},
                is_proxied_request=True,
            )

    @override_settings(LEDGER_CHANNELS={CHANNEL: {"model_export_enabled": True}})
    def test_model_download_by_classic_user_enabled(self):
        """Model export (by end-user, not proxied) with option enabled"""
        pvs = ModelPermissionViewSet()

        pvs.check_access(
            CHANNEL, User(), {"key": MODEL_KEY, "permissions": {"download": {"public": True}}}, is_proxied_request=False
        )

        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                User(),
                {"key": MODEL_KEY, "permissions": {"download": {"public": False, "authorized_ids": []}}},
                is_proxied_request=False,
            )

    @override_settings(LEDGER_CHANNELS={CHANNEL: {"model_export_enabled": False}})
    def test_model_download_by_classic_user_disabled(self):
        """Model export (by end-user, not proxied) with option disabled"""
        pvs = ModelPermissionViewSet()

        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                User(),
                {"key": MODEL_KEY, "permissions": {"process": {"public": True}}},
                is_proxied_request=False,
            )

    @override_settings(LEDGER_CHANNELS={CHANNEL: {}})
    def test_model_download_by_classic_user_default(self):
        pvs = ModelPermissionViewSet()

        # Access to model download should be denied because the "model_export_enabled"
        # option is not specified in the app configuration.
        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                User(),
                {"key": MODEL_KEY, "permissions": {"process": {"public": True}}},
                is_proxied_request=False,
            )

    @parameterized.expand(
        [
            ("one_page_test", 4, 1, 0, 4),
            ("one_element_per_page_page_two", 1, 2, 1, 2),
            ("two_element_per_page_page_two", 2, 2, 2, 4),
        ]
    )
    def test_model_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        models = assets.get_models()
        o_models = copy.deepcopy(models)
        url = reverse("substrapp:model-list")
        url = f"{url}?page_size={page_size}&page={page_number}"
        with mock.patch.object(OrchestratorClient, "query_models", return_value=o_models):
            response = self.client.get(url, **self.extra)
        r = response.json()
        self.assertContains(response, "count", 1)
        self.assertContains(response, "next", 1)
        self.assertContains(response, "previous", 1)
        self.assertContains(response, "results", 1)
        self.assertEqual(r["results"], models[index_down:index_up])

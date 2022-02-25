import logging
import os
import shutil
import tempfile
from operator import itemgetter
from unittest import mock

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from localrep.models import Model as ModelRep
from localrep.serializers import AlgoSerializer as AlgoRepSerializer
from localrep.serializers import ComputePlanSerializer as ComputePlanRepSerializer
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from localrep.serializers import DataManagerSerializer as DataManagerRepSerializer
from node.authentication import NodeUser
from substrapp.views.model import ModelPermissionViewSet
from substrapp.views.utils import AssetPermissionError

from .. import assets
from ..common import AuthenticatedClient
from ..common import get_sample_model
from ..common import internal_server_error_on_exception
from .test_views_computetask import clean_input_data
from .test_views_computetask import create_output_assets

CHANNEL = "mychannel"
TEST_ORG = "MyTestOrg"
MODEL_KEY = "some-key"
MEDIA_ROOT = tempfile.mkdtemp()


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
        self.url = reverse("substrapp:model-list")

        self.algos = assets.get_algos()
        for algo in self.algos:
            serializer = AlgoRepSerializer(data={"channel": "mychannel", **algo})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.data_managers = assets.get_data_managers()
        for data_manager in self.data_managers:
            serializer = DataManagerRepSerializer(data={"channel": "mychannel", **data_manager})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.compute_plans = assets.get_compute_plans()
        for compute_plan in self.compute_plans:
            serializer = ComputePlanRepSerializer(data={"channel": "mychannel", **compute_plan})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.compute_tasks = assets.get_train_tasks()
        self.models = []
        for compute_task in self.compute_tasks:
            cleaned_compute_task = clean_input_data(compute_task)
            serializer = ComputeTaskRepSerializer(data={"channel": "mychannel", **cleaned_compute_task})
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if compute_task["status"] == "STATUS_DONE":
                create_output_assets(compute_task)
                self.models += compute_task["train"]["models"]
        self.models.sort(key=itemgetter("creation_date", "key"))

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    def test_model_list_empty(self):
        ModelRep.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_model_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(), {"count": len(self.models), "next": None, "previous": None, "results": self.models}
        )

    def test_model_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.model.ModelViewSet.list", side_effect=Exception("Unexpected error"))
    def test_model_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_model_list_storage_addresses_update(self):
        for model in ModelRep.objects.all():
            model.model_address.replace("http://testserver", "http://remotetestserver")
            model.save()

        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.data["count"], len(self.models))
        for result, model in zip(response.data["results"], self.models):
            self.assertEqual(result["address"]["storage_address"], model["address"]["storage_address"])

    def test_model_list_filter(self):
        """Filter model on key."""
        key = self.models[0]["key"]
        params = urlencode({"search": f"model:key:{key}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 1, "next": None, "previous": None, "results": self.models[:1]})

    def test_model_list_filter_and(self):
        """Filter model on key and owner."""
        key, owner = self.models[0]["key"], self.models[0]["owner"]
        params = urlencode({"search": f"model:key:{key},model:owner:{owner}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 1, "next": None, "previous": None, "results": self.models[:1]})

    def test_model_list_filter_or(self):
        """Filter model on key_0 or key_1."""
        key_0 = self.models[0]["key"]
        key_1 = self.models[1]["key"]
        params = urlencode({"search": f"model:key:{key_0}-OR-model:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 2, "next": None, "previous": None, "results": self.models[:2]})

    def test_model_list_filter_or_and(self):
        """Filter model on (key_0 and owner_0) or (key_1 and owner_1)."""
        key_0, owner_0 = self.models[0]["key"], self.models[0]["owner"]
        key_1, owner_1 = self.models[1]["key"], self.models[1]["owner"]
        params = urlencode(
            {"search": f"model:key:{key_0},model:owner:{owner_0}-OR-model:key:{key_1},model:owner:{owner_1}"}
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 2, "next": None, "previous": None, "results": self.models[:2]})

    @parameterized.expand(
        [
            ("MODEL_UNKNOWN",),
            ("MODEL_SIMPLE",),
            ("MODEL_HEAD",),
        ]
    )
    def test_model_list_filter_by_category(self, category):
        """Filter model on category."""
        filtered_models = [task for task in self.models if task["category"] == category]
        params = urlencode({"search": f"model:category:{category}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(filtered_models), "next": None, "previous": None, "results": filtered_models},
        )

    @parameterized.expand(
        [
            ("page_size_5_page_1", 5, 1),
            ("page_size_1_page_2", 1, 2),
            ("page_size_2_page_3", 2, 3),
        ]
    )
    def test_model_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        self.assertEqual(r["count"], len(self.models))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.models[offset : offset + page_size])

    def test_model_retrieve(self):
        url = reverse("substrapp:model-detail", args=[self.models[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.models[0])

    def test_model_retrieve_wrong_channel(self):
        url = reverse("substrapp:model-detail", args=[self.models[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_model_retrieve_storage_addresses_update(self):
        model = ModelRep.objects.get(key=self.models[0]["key"])
        model.model_address.replace("http://testserver", "http://remotetestserver")
        model.save()

        url = reverse("substrapp:model-detail", args=[self.models[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.data["address"]["storage_address"], self.models[0]["address"]["storage_address"])

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.model.ModelViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_model_retrieve_fail(self, _):
        url = reverse("substrapp:model-detail", args=[self.models[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

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

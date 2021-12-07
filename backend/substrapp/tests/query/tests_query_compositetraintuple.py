import os
import shutil
import tempfile
import uuid
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from node.authentication import NodeUser
from orchestrator.client import OrchestratorClient
from substrapp.models import Metric
from substrapp.models import Model
from substrapp.utils import compute_hash

from ..common import DEFAULT_STORAGE_ADDRESS
from ..common import AuthenticatedClient
from ..common import get_sample_metric
from ..common import get_sample_model

TEST_ORG = "MyTestOrg"
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    LEDGER_MSP_ID=TEST_ORG,
)
class CompositeTraintupleQueryTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        (
            self.metric_description,
            self.metric_description_filename,
            self.metric_metrics,
            self.metric_metrics_filename,
        ) = get_sample_metric()

        self.train_data_sample_keys = ["5c1d9cd1-c2c1-082d-de09-21b56d11030c"]
        self.fake_key = "5c1d9cd1-c2c1-082d-de09-21b56d11030c"

        self.url = reverse("substrapp:composite_traintuple-list")

        self.model, _ = get_sample_model()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    @parameterized.expand([("with_in_models_and_cp", True, True), ("without_in_models", False, False)])
    def test_add_compositetraintuple_ok(self, _, with_in_models, with_compute_plan):
        # Add associated metric
        description, _, metrics, _ = get_sample_metric()
        Metric.objects.create(description=description, address=metrics)
        # post data
        url = reverse("substrapp:composite_traintuple-list")

        data = {
            "train_data_sample_keys": self.train_data_sample_keys,
            "algo_key": self.fake_key,
            "data_manager_key": self.fake_key,
            "metric_key": self.fake_key,
            "out_trunk_model_permissions": {
                "public": False,
                "authorized_ids": ["Node-1", "Node-2"],
            },
        }

        if with_in_models:
            data["in_head_model_key"] = self.fake_key
            data["in_trunk_model_key"] = self.fake_key

        if with_compute_plan:
            data["compute_plan_key"] = self.fake_key

        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch.object(OrchestratorClient, "register_tasks") as mregister_task:
            with mock.patch.object(OrchestratorClient, "register_compute_plan") as mregister_compute_plan:
                response = self.client.post(url, data, format="json", **extra)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(mregister_task.call_count, 1)
                if with_compute_plan:
                    self.assertEqual(mregister_compute_plan.call_count, 0)
                else:
                    self.assertEqual(mregister_compute_plan.call_count, 1)

    def test_add_compositetraintuple_ko(self):
        data = {"train_data_sample_keys": self.train_data_sample_keys, "in_head_model_key": self.fake_key}

        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        response = self.client.post(self.url, data, format="multipart", **extra)
        self.assertIn("This field may not be null.", response.json()["message"][0]["algo_key"])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        o = Metric.objects.create(description=self.metric_description, address=self.metric_metrics)
        data = {"metric": o.key}
        response = self.client.post(self.url, data, format="multipart", **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_head_model_ok(self):
        checksum = compute_hash(self.model.read(), key="key_traintuple")
        head_model = Model.objects.create(file=self.model, checksum=checksum, validated=True)
        model = {
            "key": "some key",
            "address": DEFAULT_STORAGE_ADDRESS,
            "permissions": {
                "process": {"public": False, "authorized_ids": ["substra"]},
                "download": {"public": False, "authorized_ids": ["substra"]},
            },
            "owner": TEST_ORG,
        }
        with mock.patch("substrapp.views.utils.get_owner", return_value=TEST_ORG), mock.patch.object(
            OrchestratorClient, "query_model", return_value=model
        ), mock.patch("substrapp.views.model.type", return_value=NodeUser):
            extra = {
                "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
                "HTTP_ACCEPT": "application/json;version=0.0",
            }
            response = self.client.get(f"/model/{head_model.key}/file/", **extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(head_model.checksum, compute_hash(response.getvalue(), key="key_traintuple"))

    def test_get_head_model_ko_user(self):
        checksum = compute_hash(self.model.read(), key="key_traintuple")
        head_model = Model.objects.create(file=self.model, checksum=checksum, validated=True)
        model = {
            "key": "some key",
            "address": DEFAULT_STORAGE_ADDRESS,
            "permissions": {
                "process": {"public": False, "authorized_ids": ["substra"]},
                "download": {"public": False, "authorized_ids": ["substra"]},
            },
            "owner": TEST_ORG,
        }

        with mock.patch("substrapp.views.utils.get_owner", return_value=TEST_ORG), mock.patch.object(
            OrchestratorClient, "query_model", return_value=model
        ):

            extra = {
                "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
                "HTTP_ACCEPT": "application/json;version=0.0",
            }
            response = self.client.get(f"/model/{head_model.key}/file/", **extra)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_head_model_ko_wrong_node(self):
        checksum = compute_hash(self.model.read(), key="key_traintuple")
        head_model = Model.objects.create(file=self.model, checksum=checksum, validated=True)
        model = {
            "key": "some key",
            "owner": TEST_ORG,
            "address": DEFAULT_STORAGE_ADDRESS,
            "permissions": {
                "process": {"public": False, "authorized_ids": ["owkin"]},
                "download": {"public": False, "authorized_ids": ["owkin"]},
            },
        }
        with mock.patch("substrapp.views.utils.get_owner", return_value=TEST_ORG), mock.patch.object(
            OrchestratorClient, "query_model", return_value=model
        ), mock.patch("substrapp.views.model.type", return_value=NodeUser):

            extra = {
                "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
                "HTTP_ACCEPT": "application/json;version=0.0",
            }
            response = self.client.get(f"/model/{head_model.key}/file/", **extra)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_deleted_intermediary_model(self):
        # When disabled the model has no storage address
        model = {
            "key": uuid.uuid4(),
            "owner": TEST_ORG,
            "permissions": {
                "process": {
                    "public": True,
                },
                "download": {
                    "public": True,
                },
            },
        }
        with mock.patch("substrapp.views.utils.get_owner", return_value=TEST_ORG), mock.patch.object(
            OrchestratorClient, "query_model", return_value=model
        ), mock.patch("substrapp.views.model.type", return_value=NodeUser):
            extra = {
                "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
                "HTTP_ACCEPT": "application/json;version=0.0",
            }
            response = self.client.get(f'/model/{model["key"]}/file/', **extra)
            self.assertEqual(response.status_code, status.HTTP_410_GONE)

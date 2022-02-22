import os
import shutil
import tempfile
import uuid
from unittest import mock

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from node.authentication import NodeUser
from orchestrator.client import OrchestratorClient
from substrapp.models import Model
from substrapp.utils import compute_hash

from ..common import DEFAULT_STORAGE_ADDRESS
from ..common import AuthenticatedClient
from ..common import get_sample_model

TEST_ORG = "MyTestOrg"
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    LEDGER_MSP_ID=TEST_ORG,
)
class ModelQueryTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.model, _ = get_sample_model()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_get_head_model_ok(self):
        checksum = compute_hash(self.model.read(), key="key_traintuple")
        head_model = Model.objects.create(file=self.model, checksum=checksum)
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
        head_model = Model.objects.create(file=self.model, checksum=checksum)
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
        head_model = Model.objects.create(file=self.model, checksum=checksum)
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

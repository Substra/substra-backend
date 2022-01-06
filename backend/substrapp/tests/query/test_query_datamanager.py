import json
import os
import shutil
import tempfile
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from grpc import StatusCode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from substrapp.models import DataManager
from substrapp.models import Metric
from substrapp.serializers import OrchestratorDataManagerSerializer

from ..common import AuthenticatedClient
from ..common import get_sample_datamanager
from ..common import get_sample_datamanager_metadata
from ..common import get_sample_metric

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
@override_settings(DEFAULT_DOMAIN="http://testserver")
class DataManagerQueryTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        (
            self.data_description,
            self.data_description_filename,
            self.data_data_opener,
            self.data_opener_filename,
        ) = get_sample_datamanager()

        (
            self.metric_description,
            self.metric_description_filename,
            self.metric_metrics,
            self.metric_metrics_filename,
        ) = get_sample_metric()

        self.url = reverse("substrapp:data_manager-list")

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def get_default_datamanager_data(self, with_test_metric=False):
        json_ = {
            "name": "slide opener",
            "type": "images",
            "permissions": {
                "public": True,
                "authorized_ids": [],
            },
            "metric_key": None,
            "logs_permission": {
                "public": True,
                "authorized_ids": [],
            },
        }

        if with_test_metric:
            json_["metric_key"] = "5c1d9cd1-c2c1-082d-de09-21b56d11030c"

        return {"json": json.dumps(json_), "description": self.data_description, "data_opener": self.data_data_opener}

    def add_default_metric(self):
        metric = Metric.objects.create(description=self.metric_description, address=self.metric_metrics)

        self.metric_key = str(metric.key)

    @parameterized.expand([("with_test_metric", True), ("without_test_metric", False)])
    def test_add_datamanager_ok(self, _, with_test_metric):
        self.add_default_metric()
        data = self.get_default_datamanager_data(with_test_metric)

        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch.object(OrchestratorClient, "register_datamanager", return_value={"key": "some key"}):
            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertIsNotNone(response.json()["key"])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_datamanager_ko(self):
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        error = OrcError()
        error.details = "OE0006"
        error.code = StatusCode.ALREADY_EXISTS

        # already exists
        with mock.patch.object(OrchestratorDataManagerSerializer, "create", side_effect=error):
            response = self.client.post(self.url, self.get_default_datamanager_data(), format="multipart", **extra)
            self.assertIn("OE0006", response.json()["message"])
            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        data = {"name": "empty datamanager"}
        response = self.client.post(self.url, data, format="multipart", **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {"description": self.data_description, "data_opener": self.data_data_opener}
        response = self.client.post(self.url, data, format="multipart", **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_datamanager_opener(self):
        datamanager = DataManager.objects.create(
            name="slide opener", description=self.data_description, data_opener=self.data_data_opener
        )

        with mock.patch("substrapp.views.utils.get_owner", return_value="foo"), mock.patch.object(
            OrchestratorClient, "query_datamanager", return_value=get_sample_datamanager_metadata()
        ):

            extra = {
                "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
                "HTTP_ACCEPT": "application/json;version=0.0",
            }
            response = self.client.get(f"/data_manager/{datamanager.key}/opener/", **extra)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(self.data_opener_filename, response.filename)

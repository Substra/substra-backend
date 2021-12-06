import json
import os
import shutil
import tempfile
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from grpc import StatusCode
from rest_framework import status
from rest_framework.test import APITestCase

from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from substrapp.models import DataManager
from substrapp.models import Metric
from substrapp.serializers import OrchestratorMetricSerializer

from ..common import AuthenticatedClient
from ..common import get_sample_datamanager
from ..common import get_sample_metric
from ..common import get_sample_metric_metadata

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
)
@override_settings(DEFAULT_DOMAIN="http://testserver")
class MetricQueryTests(APITestCase):
    client_class = AuthenticatedClient
    data_manager_key = None

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        (
            self.metric_description,
            self.metric_description_filename,
            self.metric_metrics,
            self.metric_metrics_filename,
        ) = get_sample_metric()

        (
            self.data_description,
            self.data_description_filename,
            self.data_data_opener,
            self.data_opener_filename,
        ) = get_sample_datamanager()

        self.test_data_sample_keys = ["5c1d9cd1-c2c1-082d-de09-21b56d11030c", "5c1d9cd1-c2c1-082d-de09-21b56d11030d"]

        self.url = reverse("substrapp:metric-list")

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def add_default_data_manager(self):
        dm = DataManager.objects.create(
            name="slide opener", description=self.data_description, data_opener=self.data_data_opener
        )
        self.data_manager_key = str(dm.key)

    def get_default_metric_data(self):

        json_ = {
            "name": "tough metric",
            "permissions": {
                "public": True,
                "authorized_ids": [],
            },
        }
        return {
            "description": self.metric_description,
            "file": self.metric_metrics,
            "json": json.dumps(json_),
        }

    def test_add_metric_ok(self):
        self.add_default_data_manager()
        data = self.get_default_metric_data()

        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch.object(OrchestratorClient, "register_metric", return_value={"key": "some key"}):
            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertIsNotNone(response.json()["key"])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_metric_ko(self):
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        error = OrcError()
        error.details = "OE0006"
        error.code = StatusCode.ALREADY_EXISTS

        # already exists
        with mock.patch.object(OrchestratorMetricSerializer, "create", side_effect=error):
            response = self.client.post(self.url, self.get_default_metric_data(), format="multipart", **extra)
            self.assertIn("OE0006", response.json()["message"])
            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        data = {"name": "empty metric"}
        response = self.client.post(self.url, data, format="multipart", **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {"file": self.metric_metrics, "description": self.metric_description}
        response = self.client.post(self.url, data, format="multipart", **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_metric_metrics(self):
        metric = Metric.objects.create(description=self.metric_description, address=self.metric_metrics)

        with mock.patch("substrapp.views.utils.get_owner", return_value="foo"), mock.patch.object(
            OrchestratorClient, "query_metric", return_value=get_sample_metric_metadata()
        ):

            extra = {
                "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
                "HTTP_ACCEPT": "application/json;version=0.0",
            }
            response = self.client.get(f"/metric/{metric.key}/metrics/", **extra)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(self.metric_metrics_filename, response.filename)

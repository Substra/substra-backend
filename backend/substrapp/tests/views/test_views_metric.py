import json
import logging
import os
import shutil
import tempfile
import zipfile
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from grpc import StatusCode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from localrep.models import Metric as MetricRep
from localrep.serializers import MetricSerializer as MetricRepSerializer
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError

from .. import assets
from ..common import AuthenticatedClient
from ..common import internal_server_error_on_exception

MEDIA_ROOT = tempfile.mkdtemp()
CHANNEL = "mychannel"

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURE_PATH = os.path.join(DIR_PATH, "../../../../fixtures/owkin/metrics/metric0")


def zip_folder(path, destination):
    zipf = zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for f in files:
            abspath = os.path.join(root, f)
            archive_path = os.path.relpath(abspath, start=path)
            zipf.write(abspath, arcname=archive_path)
    zipf.close()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
@override_settings(DEFAULT_DOMAIN="https://localhost")
class MetricViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.url = reverse("substrapp:metric-list")
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

        self.metrics = assets.get_metrics()
        for metric in self.metrics:
            serializer = MetricRepSerializer(data={"channel": "mychannel", **metric})
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_metric_list_empty(self):
        MetricRep.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_metric_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(), {"count": len(self.metrics), "next": None, "previous": None, "results": self.metrics}
        )

    def test_metric_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.metric.MetricViewSet.list", side_effect=Exception("Unexpected error"))
    def test_metric_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @mock.patch("substrapp.views.metric.node_client.get", return_value=b"content")
    def test_metric_list_storage_addresses_update(self, _):
        for metric in MetricRep.objects.all():
            metric.description_address.replace("http://testserver", "http://remotetestserver")
            metric.metric_address.replace("http://testserver", "http://remotetestserver")
            metric.save()

        response = self.client.get(self.url, **self.extra)
        self.assertEqual(len(response.data["results"]), len(self.metrics))
        for result, metric in zip(response.data["results"], self.metrics):
            for field in ("description", "address"):
                self.assertEqual(result[field]["storage_address"], metric[field]["storage_address"])

    def test_metric_list_filter_and(self):
        """Filter metric on key and owner."""
        key, owner = self.metrics[0]["key"], self.metrics[0]["owner"]
        params = urlencode({"search": f"metric:key:{key},metric:owner:{owner}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 1, "next": None, "previous": None, "results": self.metrics[:1]})

    def test_metric_list_filter_or(self):
        """Filter metric on key_0 or key_1."""
        key_0 = self.metrics[0]["key"]
        key_1 = self.metrics[1]["key"]
        params = urlencode({"search": f"metric:key:{key_0}-OR-metric:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 2, "next": None, "previous": None, "results": self.metrics[:2]})

    def test_metric_list_filter_or_and(self):
        """Filter metric on (key_0 and owner_0) or (key_1 and owner_1)."""
        key_0, owner_0 = self.metrics[0]["key"], self.metrics[0]["owner"]
        key_1, owner_1 = self.metrics[1]["key"], self.metrics[1]["owner"]
        params = urlencode(
            {"search": f"metric:key:{key_0},metric:owner:{owner_0}-OR-metric:key:{key_1},metric:owner:{owner_1}"}
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json(), {"count": 2, "next": None, "previous": None, "results": self.metrics[:2]})

    @parameterized.expand(
        [
            ("page_size_5_page_1", 5, 1),
            ("page_size_1_page_2", 1, 2),
            ("page_size_2_page_3", 2, 3),
        ]
    )
    def test_metric_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        self.assertEqual(r["count"], len(self.metrics))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.metrics[offset : offset + page_size])

    def test_metric_create(self):
        def mock_orc_response(data):
            """Build orchestrator register response from request data."""
            return {
                "key": data["key"],
                "name": data["name"],
                "owner": data["new_permissions"]["authorized_ids"][0],
                "permissions": {
                    "process": data["new_permissions"],
                    "download": data["new_permissions"],
                },
                "metadata": {},
                "creation_date": "2021-11-04T13:54:09.882662Z",
                "description": data["description"],
                "address": data["address"],
            }

        metric_path = os.path.join(FIXTURE_PATH, "metrics.zip")
        description_path = os.path.join(FIXTURE_PATH, "description.md")
        data = {
            "json": json.dumps(
                {
                    "name": "Simplified skin lesion classification",
                    "permissions": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                }
            ),
            "file": open(metric_path, "rb"),
            "description": open(description_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_metric", side_effect=mock_orc_response):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        self.assertIsNotNone(response.data["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # asset created in local db
        self.assertEqual(MetricRep.objects.count(), len(self.metrics) + 1)

        data["file"].close()
        data["description"].close()

    @override_settings(DATA_UPLOAD_MAX_SIZE=150)
    def test_file_size_limit(self):
        metric_path = os.path.join(FIXTURE_PATH, "metrics.zip")
        description_path = os.path.join(FIXTURE_PATH, "description.md")
        data = {
            "json": json.dumps(
                {
                    "name": "Simplified skin lesion classification",
                    "permissions": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                }
            ),
            "file": open(metric_path, "rb"),
            "description": open(description_path, "rb"),
        }

        response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File too large", response.data["message"][0]["address"])

        data["description"].close()
        data["file"].close()

    def test_metric_create_fail_rollback(self):
        class MockOrcError(OrcError):
            code = StatusCode.ALREADY_EXISTS
            details = "already exists"

        metric_path = os.path.join(FIXTURE_PATH, "metrics.zip")
        description_path = os.path.join(FIXTURE_PATH, "description.md")
        data = {
            "json": json.dumps(
                {
                    "name": "Simplified skin lesion classification",
                    "permissions": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                }
            ),
            "file": open(metric_path, "rb"),
            "description": open(description_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_metric", side_effect=MockOrcError()):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        # asset not created in local db
        self.assertEqual(MetricRep.objects.count(), len(self.metrics))
        # orc error code should be propagated
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.metric.MetricViewSet.create", side_effect=Exception("Unexpected error"))
    def test_metric_create_fail(self, _):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @mock.patch("substrapp.views.metric.node_client.get", return_value=b"content")
    def test_metric_retrieve(self, _):
        url = reverse("substrapp:metric-detail", args=[self.metrics[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.metrics[0])

    def test_metric_retrieve_wrong_channel(self):
        url = reverse("substrapp:metric-detail", args=[self.metrics[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @parameterized.expand([(True,), (False,)])
    @mock.patch("substrapp.views.metric.node_client.get", return_value=b"content")
    def test_metric_retrieve_storage_addresses_update(self, has_cache, _):
        metric = MetricRep.objects.get(key=self.metrics[0]["key"])
        metric.description_address.replace("http://testserver", "http://remotetestserver")
        metric.metric_address.replace("http://testserver", "http://remotetestserver")
        metric.save()

        url = reverse("substrapp:metric-detail", args=[self.metrics[0]["key"]])
        with mock.patch("substrapp.views.metric.node_has_process_permission", return_value=has_cache):
            response = self.client.get(url, **self.extra)
        for field in ("description", "address"):
            self.assertEqual(response.data[field]["storage_address"], self.metrics[0][field]["storage_address"])

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.metric.MetricViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_metric_retrieve_fail(self, _):
        url = reverse("substrapp:metric-detail", args=[self.metrics[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

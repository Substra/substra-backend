import copy
import json
import logging
import os
import shutil
import tempfile
import zipfile
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from grpc import StatusCode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

import orchestrator.error
from orchestrator.client import OrchestratorClient

from .. import assets
from ..common import AuthenticatedClient
from ..common import encode_filter
from ..common import get_sample_metric
from ..common import internal_server_error_on_exception

MEDIA_ROOT = tempfile.mkdtemp()
CHANNEL = "mychannel"


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
        (
            self.metric_description,
            self.metric_description_filename,
            self.metric_metrics,
            self.metric_metrics_filename,
        ) = get_sample_metric()

        self.test_data_sample_keys = ["2d0f943a-a81a-9cb3-fe84-b162559ce6af", "533ee6e7-b9d8-b247-e7e8-53b24547f57e"]

        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_metric_list_empty(self):
        with mock.patch.object(OrchestratorClient, "query_metrics", return_value=[]):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r, {"count": 0, "next": None, "previous": None, "results": []})

    def test_metric_list_success(self):
        metrics = assets.get_metrics()
        expected = copy.deepcopy(metrics)
        with mock.patch.object(OrchestratorClient, "query_metrics", return_value=metrics):
            response = self.client.get(self.url, **self.extra)
            r = response.json()
            self.assertEqual(r["results"], expected)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.metric.get_channel_name", side_effect=Exception("Unexpected error"))
    def test_metric_list_fail_internal_server_error(self, get_channel_name: mock.Mock):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        get_channel_name.assert_called_once()

    def test_metric_list_filter_fail(self):
        metrics = assets.get_metrics()
        with mock.patch.object(OrchestratorClient, "query_metrics", return_value=metrics):
            search_params = "?search=challenERRORge"
            response = self.client.get(self.url + search_params, **self.extra)
            self.assertIn("Malformed search filters", response.json()["message"])

    def test_metric_list_filter_name(self):
        metrics = assets.get_metrics()
        name_to_filter = encode_filter(metrics[0]["name"])
        with mock.patch.object(OrchestratorClient, "query_metrics", return_value=metrics):
            search_params = f"?search=metric%253Aname%253A{name_to_filter}"
            response = self.client.get(self.url + search_params, **self.extra)
            r = response.json()
            self.assertEqual(len(r["results"]), 1)

    def test_metric_retrieve(self):
        metric = assets.get_metric()
        expected = copy.deepcopy(metric)
        with open(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../../../fixtures/owkin/metrics/metric0/description.md"
            ),
            "rb",
        ) as f:
            content = f.read()

        with mock.patch.object(OrchestratorClient, "query_metric", return_value=metric), mock.patch(
            "substrapp.views.metric.node_client.get", return_value=content
        ):
            response = self.client.get(f'{self.url}{metric["key"]}/', **self.extra)
            self.assertEqual(response.json(), expected)

    def test_metric_retrieve_fail(self):
        # Key < 32 chars
        search_params = "12312323/"
        response = self.client.get(self.url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Key not hexa
        search_params = "X" * 32 + "/"
        response = self.client.get(self.url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = orchestrator.error.OrcError
        error.details = "out of range test"
        error.code = StatusCode.OUT_OF_RANGE

        metric = assets.get_metric()

        with mock.patch.object(OrchestratorClient, "query_metric", side_effect=error):
            response = self.client.get(f'{self.url}{metric["key"]}/', **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.metric.MetricViewSet._retrieve", side_effect=Exception("Unexpected error"))
    def test_metric_retrieve_fail_internal_server_error(self, _retrieve: mock.Mock):
        response = self.client.get(self.url + "123/")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        _retrieve.assert_called_once()

    def test_metric_create(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        metric_path = os.path.join(dir_path, "../../../../fixtures/owkin/metrics/metric0/")
        description_path = os.path.join(metric_path, "description.md")
        metrics_path = os.path.join(MEDIA_ROOT, "metrics.zip")
        zip_folder(metric_path, metrics_path)

        data = {
            "json": json.dumps(
                {
                    "name": "Simplified skin lesion classification",
                    "permissions": {
                        "public": True,
                        "authorized_ids": [],
                    },
                }
            ),
            "description": open(description_path, "rb"),
            "file": open(metrics_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_metric", return_value={}):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        self.assertIsNotNone(response.data["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data["description"].close()
        data["file"].close()

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.metric.MetricViewSet._create", side_effect=Exception("Unexpected error"))
    def test_metric_create_fail_internal_server_error(self, _create: mock.Mock):
        response = self.client.post(self.url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        _create.assert_called_once()

    def test_metric_list_storage_addresses_update(self):

        # mock content
        metrics = assets.get_metrics()
        o_metrics = copy.deepcopy(metrics)
        for obj in o_metrics:
            for field in ("description", "address"):
                obj[field]["storage_address"] = obj[field]["storage_address"].replace(
                    "http://testserver", "http://remotetestserver"
                )

        with mock.patch.object(OrchestratorClient, "query_metrics", return_value=o_metrics), mock.patch(
            "substrapp.views.metric.node_client.get", return_value=b"dummy binary content"
        ):
            response = self.client.get(self.url, **self.extra)
            self.assertEqual(len(response.data["results"]), len(metrics))
            for i, res_metric in enumerate(response.data["results"]):
                for field in ("description", "address"):
                    self.assertEqual(res_metric[field]["storage_address"], metrics[i][field]["storage_address"])

    def test_metric_retrieve_storage_addresses_update_with_cache(self):
        metric = assets.get_metric()
        url = reverse("substrapp:metric-detail", args=[metric["key"]])
        o_metric = copy.deepcopy(metric)
        for field in ("description", "address"):
            o_metric[field]["storage_address"] = o_metric[field]["storage_address"].replace(
                "http://testserver", "http://remotetestserver"
            )

        with mock.patch.object(OrchestratorClient, "query_metric", return_value=o_metric), mock.patch(
            "substrapp.views.metric.node_has_process_permission", return_value=True
        ), mock.patch("substrapp.views.metric.node_client.get", return_value=b"dummy binary content"):
            response = self.client.get(url, **self.extra)
            for field in ("description", "address"):
                self.assertEqual(response.data[field]["storage_address"], metric[field]["storage_address"])

    def test_metric_retrieve_storage_addresses_update_without_cache(self):
        metric = assets.get_metric()
        url = reverse("substrapp:metric-detail", args=[metric["key"]])
        o_metric = copy.deepcopy(metric)
        for field in ("description", "address"):
            o_metric[field]["storage_address"] = o_metric[field]["storage_address"].replace(
                "http://testserver", "http://remotetestserver"
            )

        with mock.patch.object(OrchestratorClient, "query_metric", return_value=o_metric), mock.patch(
            "substrapp.views.metric.node_has_process_permission", return_value=False
        ), mock.patch("substrapp.views.metric.node_client.get", return_value=b"dummy binary content"):
            response = self.client.get(url, **self.extra)
            for field in ("description", "address"):
                self.assertEqual(response.data[field]["storage_address"], metric[field]["storage_address"])

    @parameterized.expand(
        [
            ("one_page_test", 2, 1, 0, 2),
            ("one_element_per_page_page_two", 1, 2, 1, 2),
        ]
    )
    def test_metric_list_pagination_success(self, _, page_size, page_number, index_down, index_up):
        metrics = assets.get_metrics()
        expected = copy.deepcopy(metrics)
        url = reverse("substrapp:metric-list")
        url = f"{url}?page_size={page_size}&page={page_number}"
        with mock.patch.object(OrchestratorClient, "query_metrics", return_value=expected):
            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertContains(response, "count", 1)
            self.assertContains(response, "next", 1)
            self.assertContains(response, "previous", 1)
            self.assertContains(response, "results", 1)
            self.assertEqual(r["results"], metrics[index_down:index_up])

    @override_settings(DATA_UPLOAD_MAX_SIZE=150)
    def test_file_size_limit(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        metric_path = os.path.join(dir_path, "../../../../fixtures/owkin/metrics/metric0/")
        description_path = os.path.join(metric_path, "description.md")
        metrics_path = os.path.join(MEDIA_ROOT, "metrics.zip")
        zip_folder(metric_path, metrics_path)

        data = {
            "json": json.dumps(
                {
                    "name": "Simplified skin lesion classification",
                    "permissions": {
                        "public": True,
                        "authorized_ids": [],
                    },
                }
            ),
            "description": open(description_path, "rb"),
            "file": open(metrics_path, "rb"),
        }

        response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File too large", response.data["message"][0]["address"])

        data["description"].close()
        data["file"].close()

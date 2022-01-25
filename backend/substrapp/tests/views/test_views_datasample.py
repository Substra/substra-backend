import json
import logging
import ntpath
import os
import shutil
import tempfile
from unittest import mock

import django.urls
from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from grpc import StatusCode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from localrep.models import DataSample as DataSampleRep
from localrep.serializers import DataManagerSerializer as DataManagerRepSerializer
from localrep.serializers import DataSampleSerializer as DataSampleRepSerializer
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from substrapp.utils import get_dir_hash

from .. import assets
from ..common import AuthenticatedClient
from ..common import internal_server_error_on_exception

MEDIA_ROOT = tempfile.mkdtemp()
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURE_PATH = os.path.abspath(os.path.join(DIR_PATH, "../../../../fixtures/chunantes/datasamples"))


def _get_archive_checksum(path):
    with tempfile.TemporaryDirectory() as tmp_path:
        shutil.unpack_archive(path, tmp_path)
        return get_dir_hash(tmp_path)


def mock_register_datasamples(orc_request):
    """Build orchestrator register response from request data."""
    return [
        {
            "key": data["key"],
            "data_manager_keys": data["data_manager_keys"],
            "test_only": data["test_only"],
            "checksum": data["checksum"],
            "owner": "MyOrg1MSP",
            "creation_date": "2021-11-04T13:54:09.882662Z",
        }
        for data in orc_request["samples"]
    ]


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
@override_settings(DEFAULT_DOMAIN="https://localhost")
class DataSampleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.url = reverse("substrapp:data_sample-list")
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

        self.data_managers = assets.get_data_managers()
        for data_manager in self.data_managers:
            serializer = DataManagerRepSerializer(data={"channel": "mychannel", **data_manager})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.data_samples = assets.get_data_samples()
        for data_sample in self.data_samples:
            del data_sample["path"]
            serializer = DataSampleRepSerializer(data={"channel": "mychannel", **data_sample})
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    def test_datasample_list_empty(self):
        DataSampleRep.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_datasample_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.data_samples), "next": None, "previous": None, "results": self.data_samples},
        )

    def test_datasample_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.datasample.DataSampleViewSet.list", side_effect=Exception("Unexpected error"))
    def test_datasample_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_datasample_list_filter(self):
        """Filter datasample on key."""
        key = self.data_samples[0]["key"]
        params = urlencode({"search": f"datasample:key:{key}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.data_samples[:1]}
        )

    def test_datasample_list_filter_and(self):
        """Filter datasample on key and owner."""
        key, owner = self.data_samples[0]["key"], self.data_samples[0]["owner"]
        params = urlencode({"search": f"datasample:key:{key},datasample:owner:{owner}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.data_samples[:1]}
        )

    def test_datasample_list_filter_or(self):
        """Filter datasample on key_0 or key_1."""
        key_0 = self.data_samples[0]["key"]
        key_1 = self.data_samples[1]["key"]
        params = urlencode({"search": f"datasample:key:{key_0}-OR-datasample:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.data_samples[:2]}
        )

    def test_datasample_list_filter_or_and(self):
        """Filter datasample on (key_0 and owner_0) or (key_1 and owner_1)."""
        key_0, owner_0 = self.data_samples[0]["key"], self.data_samples[0]["owner"]
        key_1, owner_1 = self.data_samples[1]["key"], self.data_samples[1]["owner"]
        params = urlencode(
            {
                "search": (
                    f"datasample:key:{key_0},datasample:owner:{owner_0}"
                    f"-OR-datasample:key:{key_1},datasample:owner:{owner_1}"
                )
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.data_samples[:2]}
        )

    @parameterized.expand(
        [
            ("page_size_5_page_1", 5, 1),
            ("page_size_1_page_2", 1, 2),
            ("page_size_2_page_3", 2, 3),
        ]
    )
    def test_datasample_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        self.assertEqual(r["count"], len(self.data_samples))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.data_samples[offset : offset + page_size])

    def test_data_create_upload(self):
        """Upload single datasample."""
        data_path = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        data = {
            "file": open(data_path, "rb"),
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": False,
                }
            ),
        }

        with mock.patch.object(
            OrchestratorClient, "register_datasamples", side_effect=mock_register_datasamples
        ), mock.patch("substrapp.views.datasample.DataSampleViewSet.check_datamanagers", return_value=None):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertIsNotNone(response.data[0]["key"])
        self.assertEqual(response.data[0]["checksum"], _get_archive_checksum(data_path))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # asset created in local db
        self.assertEqual(DataSampleRep.objects.count(), len(self.data_samples) + 1)

        data["file"].close()

    def test_data_create_bulk_upload(self):
        """Upload multiple datasamples."""
        data_path1 = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        data_path2 = os.path.join(FIXTURE_PATH, "datasample0/0024899.zip")
        data = {
            "files": [path_leaf(data_path1), path_leaf(data_path2)],
            path_leaf(data_path1): open(data_path1, "rb"),
            path_leaf(data_path2): open(data_path2, "rb"),
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": False,
                }
            ),
        }

        with mock.patch.object(
            OrchestratorClient, "register_datasamples", side_effect=mock_register_datasamples
        ), mock.patch("substrapp.views.datasample.DataSampleViewSet.check_datamanagers", return_value=None):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertIsNotNone(response.data[0]["key"])
        self.assertIsNotNone(response.data[1]["key"])
        self.assertEqual(response.data[0]["checksum"], _get_archive_checksum(data_path1))
        self.assertEqual(response.data[1]["checksum"], _get_archive_checksum(data_path2))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # assets created in local db
        self.assertEqual(DataSampleRep.objects.count(), len(self.data_samples) + 2)

        for x in data["files"]:
            data[x].close()

    @override_settings(SERVERMEDIAS_ROOT=MEDIA_ROOT)
    def test_data_create_path(self):
        """Send datasample path."""
        source_path = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        target_path = os.path.join(MEDIA_ROOT, "0024700")
        shutil.unpack_archive(source_path, target_path)

        data = {
            "path": target_path,
            "data_manager_keys": [self.data_managers[0]["key"]],
            "test_only": False,
        }

        with mock.patch.object(
            OrchestratorClient, "register_datasamples", side_effect=mock_register_datasamples
        ), mock.patch("substrapp.views.datasample.DataSampleViewSet.check_datamanagers", return_value=None):
            response = self.client.post(self.url, data=data, format="json", **self.extra)

        self.assertIsNotNone(response.data[0]["key"])
        self.assertEqual(response.data[0]["checksum"], get_dir_hash(target_path))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # asset created in local db
        self.assertEqual(DataSampleRep.objects.count(), len(self.data_samples) + 1)

    @override_settings(SERVERMEDIAS_ROOT=MEDIA_ROOT)
    def test_data_create_parent_path(self):
        """Send multiple datasamples parent path."""
        parent_path = os.path.join(MEDIA_ROOT, "data_samples")
        source_path1 = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        target_path1 = os.path.join(parent_path, "0024700")
        shutil.unpack_archive(source_path1, target_path1)
        source_path2 = os.path.join(FIXTURE_PATH, "datasample0/0024899.zip")
        target_path2 = os.path.join(parent_path, "0024899")
        shutil.unpack_archive(source_path2, target_path2)

        data = {
            "path": parent_path,
            "data_manager_keys": [self.data_managers[0]["key"]],
            "test_only": False,
            "multiple": True,
        }

        with mock.patch.object(
            OrchestratorClient, "register_datasamples", side_effect=mock_register_datasamples
        ), mock.patch("substrapp.views.datasample.DataSampleViewSet.check_datamanagers", return_value=None):
            response = self.client.post(self.url, data=data, format="json", **self.extra)

        self.assertIsNotNone(response.data[0]["key"])
        self.assertIsNotNone(response.data[1]["key"])
        self.assertEqual(response.data[0]["checksum"], get_dir_hash(target_path1))
        self.assertEqual(response.data[1]["checksum"], get_dir_hash(target_path2))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # assets created in local db
        self.assertEqual(DataSampleRep.objects.count(), len(self.data_samples) + 2)

    @override_settings(DATA_UPLOAD_MAX_SIZE=150)
    def test_file_size_limit(self):
        data_path = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        data = {
            "file": open(data_path, "rb"),
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": False,
                }
            ),
        }

        with mock.patch("substrapp.views.datasample.DataSampleViewSet.check_datamanagers", return_value=None):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File too large", response.data["message"])
        data["file"].close()

    def test_data_create_fail_rollback(self):
        class MockOrcError(OrcError):
            code = StatusCode.ALREADY_EXISTS
            details = "already exists"

        data_path = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        data = {
            "file": open(data_path, "rb"),
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": False,
                }
            ),
        }

        with mock.patch.object(OrchestratorClient, "register_datasamples", side_effect=MockOrcError()), mock.patch(
            "substrapp.views.datasample.DataSampleViewSet.check_datamanagers", return_value=None
        ):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        # asset not created in local db
        self.assertEqual(DataSampleRep.objects.count(), len(self.data_samples))
        # orc error code should be propagated
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        data["file"].close()

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.datasample.DataSampleViewSet.create", side_effect=Exception("Unexpected error"))
    def test_data_create_fail_internal_server_error(self, _):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.datasample.OrchestratorDataSampleUpdateSerializer")
    @mock.patch("substrapp.views.datasample.get_channel_name", side_effect=Exception("Unexpected error"))
    def test_datasamples_bulk_update_fail_internal_server_error(
        self, serializer_constructor: mock.Mock, get_channel_name: mock.Mock
    ):
        data_sample_serializer = mock.Mock()
        serializer_constructor.return_value = data_sample_serializer

        url = django.urls.reverse("substrapp:data_sample-bulk-update")
        response = self.client.post(url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        get_channel_name.assert_called_once()


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

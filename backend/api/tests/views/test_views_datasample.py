import json
import logging
import ntpath
import os
import shutil
import tempfile
from unittest import mock

import django.urls
from django.core.serializers.json import DjangoJSONEncoder
from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from grpc import StatusCode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import DataSample
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient
from api.tests.common import internal_server_error_on_exception
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from substrapp.utils import get_dir_hash

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
            "checksum": data["checksum"],
            "owner": "MyOrg1MSP",
            "creation_date": "2021-11-04T13:54:09.882662Z",
        }
        for data in orc_request["samples"]
    ]


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    CHANNELS={"mychannel": {"model_export_enabled": True}},
)
@override_settings(DEFAULT_DOMAIN="https://localhost")
class DataSampleViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.url = reverse("api:data_sample-list")
        self.extra = {"HTTP_ACCEPT": "application/json;version=0.0"}

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

        data_manager = factory.create_datamanager()
        data_manager_2 = factory.create_datamanager()
        self.data_manager_key = data_manager.key

        train_data_sample_1 = factory.create_datasample([data_manager])
        train_data_sample_2 = factory.create_datasample([data_manager_2])
        test_data_sample = factory.create_datasample([data_manager_2])

        self.function = factory.create_function()
        self.compute_plan = factory.create_computeplan()
        factory.create_computetask(self.compute_plan, self.function)
        self.expected_results = [
            {
                "key": str(train_data_sample_1.key),
                "owner": "MyOrg1MSP",
                "data_manager_keys": [str(data_manager.key)],
                "creation_date": train_data_sample_1.creation_date.isoformat().replace("+00:00", "Z"),
            },
            {
                "key": str(train_data_sample_2.key),
                "owner": "MyOrg1MSP",
                "data_manager_keys": [str(data_manager_2.key)],
                "creation_date": train_data_sample_2.creation_date.isoformat().replace("+00:00", "Z"),
            },
            {
                "key": str(test_data_sample.key),
                "owner": "MyOrg1MSP",
                "data_manager_keys": [str(data_manager_2.key)],
                "creation_date": test_data_sample.creation_date.isoformat().replace("+00:00", "Z"),
            },
        ]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    def test_datasample_retrieve(self):
        url = reverse("api:data_sample-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.expected_results[0])

    def test_datasample_retrieve_wrong_channel(self):
        url = reverse("api:data_sample-detail", args=[self.expected_results[0]["key"]])
        self.client.channel = "yourchannel"
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @internal_server_error_on_exception()
    @mock.patch("api.views.datasample.DataSampleViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_datasample_retrieve_fail(self, _):
        url = reverse("api:data_sample-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_datasample_list_empty(self):
        DataSample.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_datasample_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_datasample_list_wrong_channel(self):
        self.client.channel = "yourchannel"
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("api.views.datasample.DataSampleViewSet.list", side_effect=Exception("Unexpected error"))
    def test_datasample_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_datasample_list_filter(self):
        """Filter datasample on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_datasample_list_filter_and(self):
        """Filter datasample on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"key": key, "owner": owner})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_datasample_list_filter_in(self):
        """Filter datasample in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_datasample_list_cross_assets_filters(self):
        """Filter datasample on other asset key such as compute_plan_key, function_key and dataset_key"""

        # filter on dataset_key
        params = urlencode({"dataset_key": str(self.data_manager_key)})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results[:1])

    def test_datasample_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results)

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results[::-1])

    @parameterized.expand(
        [
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_datasample_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_data_create_upload(self):
        """Upload single datasample."""
        data_path = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        data = {
            "file": open(data_path, "rb"),
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_manager_key],
                },
                cls=DjangoJSONEncoder,
            ),
        }

        with (
            mock.patch.object(OrchestratorClient, "register_datasamples", side_effect=mock_register_datasamples),
            mock.patch("api.views.datasample.check_datamanagers", return_value=None),
        ):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertIsNotNone(response.data[0]["key"])
        self.assertEqual(response.data[0]["checksum"], _get_archive_checksum(data_path))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # asset created in local db
        self.assertEqual(DataSample.objects.count(), len(self.expected_results) + 1)

        data["file"].close()

    def test_datasample_create_bulk_upload(self):
        """Upload multiple datasamples."""
        data_path1 = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        data_path2 = os.path.join(FIXTURE_PATH, "datasample0/0024899.zip")
        data = {
            "files": [path_leaf(data_path1), path_leaf(data_path2)],
            path_leaf(data_path1): open(data_path1, "rb"),
            path_leaf(data_path2): open(data_path2, "rb"),
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_manager_key],
                },
                cls=DjangoJSONEncoder,
            ),
        }

        with (
            mock.patch.object(OrchestratorClient, "register_datasamples", side_effect=mock_register_datasamples),
            mock.patch("api.views.datasample.check_datamanagers", return_value=None),
        ):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertIsNotNone(response.data[0]["key"])
        self.assertIsNotNone(response.data[1]["key"])
        self.assertEqual(response.data[0]["checksum"], _get_archive_checksum(data_path1))
        self.assertEqual(response.data[1]["checksum"], _get_archive_checksum(data_path2))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # assets created in local db
        self.assertEqual(DataSample.objects.count(), len(self.expected_results) + 2)

        for x in data["files"]:
            data[x].close()

    @override_settings(SERVERMEDIAS_ROOT=MEDIA_ROOT)
    def test_datasample_create_path(self):
        """Send datasample path."""
        source_path = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        target_path = os.path.join(MEDIA_ROOT, "0024700")
        shutil.unpack_archive(source_path, target_path)

        data = {
            "path": target_path,
            "data_manager_keys": [self.data_manager_key],
        }

        with (
            mock.patch.object(OrchestratorClient, "register_datasamples", side_effect=mock_register_datasamples),
            mock.patch("api.views.datasample.check_datamanagers", return_value=None),
        ):
            response = self.client.post(self.url, data=data, format="json", **self.extra)

        self.assertIsNotNone(response.data[0]["key"])
        self.assertEqual(response.data[0]["checksum"], get_dir_hash(target_path))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # asset created in local db
        self.assertEqual(DataSample.objects.count(), len(self.expected_results) + 1)

    @override_settings(SERVERMEDIAS_ROOT=MEDIA_ROOT)
    def test_datasample_create_parent_path(self):
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
            "data_manager_keys": [self.data_manager_key],
            "multiple": True,
        }

        with (
            mock.patch.object(OrchestratorClient, "register_datasamples", side_effect=mock_register_datasamples),
            mock.patch("api.views.datasample.check_datamanagers", return_value=None),
        ):
            response = self.client.post(self.url, data=data, format="json", **self.extra)

        self.assertIsNotNone(response.data[0]["key"])
        self.assertIsNotNone(response.data[1]["key"])
        self.assertEqual(
            set([response.data[0]["checksum"], response.data[1]["checksum"]]),
            set([get_dir_hash(target_path1), get_dir_hash(target_path2)]),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # assets created in local db
        self.assertEqual(DataSample.objects.count(), len(self.expected_results) + 2)

    @override_settings(DATA_UPLOAD_MAX_SIZE=150)
    def test_file_size_limit(self):
        data_path = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        data = {
            "file": open(data_path, "rb"),
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_manager_key],
                },
                cls=DjangoJSONEncoder,
            ),
        }

        with mock.patch("api.views.datasample.check_datamanagers", return_value=None):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File too large", response.data["detail"])
        data["file"].close()

    def test_datasample_create_fail_rollback(self):
        class MockOrcError(OrcError):
            def __init__(self) -> None:
                pass

            code = StatusCode.ALREADY_EXISTS
            details = "already exists"

        data_path = os.path.join(FIXTURE_PATH, "datasample1/0024700.zip")
        data = {
            "file": open(data_path, "rb"),
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_manager_key],
                },
                cls=DjangoJSONEncoder,
            ),
        }

        with (
            mock.patch.object(OrchestratorClient, "register_datasamples", side_effect=MockOrcError()),
            mock.patch("api.views.datasample.check_datamanagers", return_value=None),
        ):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        # asset not created in local db
        self.assertEqual(DataSample.objects.count(), len(self.expected_results))
        # orc error code should be propagated
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        data["file"].close()

    @internal_server_error_on_exception()
    @mock.patch("api.views.datasample.DataSampleViewSet.create", side_effect=Exception("Unexpected error"))
    def test_datasample_create_fail(self, _):
        response = self.client.post(self.url, data={}, format="json", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @internal_server_error_on_exception()
    @mock.patch("api.views.datasample.get_channel_name", side_effect=Exception("Unexpected error"))
    def test_datasample_bulk_update_fail(self, get_channel_name: mock.Mock):
        url = django.urls.reverse("api:data_sample-bulk-update")
        response = self.client.post(url, data={}, format="json", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        get_channel_name.assert_called_once()

    def test_datasample_bulk_update(self):
        data_manager_1 = factory.create_datamanager()
        data_manager_2 = factory.create_datamanager()
        data = {
            "data_manager_keys": [str(data_manager_1.key), str(data_manager_2.key)],
            "data_sample_keys": [data_sample["key"] for data_sample in self.expected_results],
        }
        url = django.urls.reverse("api:data_sample-bulk-update")
        with mock.patch.object(OrchestratorClient, "update_datasample", return_value={}):
            response = self.client.post(url, data=data, format="json", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

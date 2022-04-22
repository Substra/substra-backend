import json
import os
import shutil
import tempfile
import zipfile
from unittest import mock
from unittest.mock import MagicMock

from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import override_settings
from django.urls import reverse
from grpc import StatusCode
from rest_framework import status
from rest_framework.test import APITestCase

from localrep.serializers import DataManagerSerializer as DataManagerRepSerializer
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from substrapp.models import DataSample
from substrapp.serializers import DataSampleSerializer
from substrapp.tests import assets

from ..common import AuthenticatedClient
from ..common import get_sample_script
from ..common import get_sample_tar_data_sample
from ..common import get_sample_zip_data_sample
from ..common import get_sample_zip_data_sample_2

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURE_PATH = os.path.abspath(os.path.join(DIR_PATH, "../../../../fixtures/owkin"))
MEDIA_ROOT = tempfile.mkdtemp()


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


@mock.patch.object(OrchestratorClient, "register_datasamples", side_effect=mock_register_datasamples)
@mock.patch("substrapp.views.datasample.check_datamanagers", return_value=None)
@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
@override_settings(DEFAULT_DOMAIN="http://testserver")
class DataSampleQueryTests(APITestCase):
    client_class = AuthenticatedClient

    data_manager_key1 = None
    data_manager_key2 = None

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.script, self.script_filename = get_sample_script()
        self.data_file, self.data_file_filename = get_sample_zip_data_sample()
        self.data_file_2, self.data_file_filename_2 = get_sample_zip_data_sample_2()
        self.data_tar_file, self.data_tar_file_filename = get_sample_tar_data_sample()

        self.url = reverse("substrapp:data_sample-list")
        self.extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        self.data_managers = assets.get_data_managers()
        for data_manager in self.data_managers:
            serializer = DataManagerRepSerializer(data={"channel": "mychannel", **data_manager})
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def get_default_datasample_data(self):
        self.data_file.file.seek(0)
        return {
            "file": self.data_file,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": True,
                }
            ),
        }

    def test_add_data_sample_from_upload_sync_ok(self, *_):
        data = self.get_default_datasample_data()
        response = self.client.post(self.url, data, format="multipart", **self.extra)
        self.assertIsNotNone(response.json()[0]["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(SERVERMEDIAS_ROOT=FIXTURE_PATH)
    def _test_add_datasample_from_path_sync_ok(self):
        path = os.path.join(FIXTURE_PATH, "datasamples/test/0024900")
        data = {
            "json": json.dumps(
                {
                    "path": path,
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": True,
                }
            ),
        }
        response = self.client.post(self.url, data, format="multipart", **self.extra)
        jsonr = response.json()
        self.assertIsNotNone(jsonr[0]["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # sensitive data should never be served by the API.
        self.assertNotIn("file", jsonr[0])

    def test_bulk_add_data_sample_ok(self, *_):
        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.read())

        file_mock2 = MagicMock(spec=InMemoryUploadedFile)
        file_mock2.name = "bar.zip"
        file_mock2.read = MagicMock(return_value=self.data_file_2.read())

        data = {
            file_mock.name: file_mock,
            file_mock2.name: file_mock2,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"], self.data_managers[1]["key"]],
                    "test_only": True,
                }
            ),
        }
        self.data_file.seek(0)
        self.data_file_2.seek(0)

        response = self.client.post(self.url, data, format="multipart", **self.extra)
        r = response.json()

        self.assertEqual(len(r), 2)
        self.assertIsNotNone(r[0]["key"])
        self.assertIsNotNone(r[1]["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS=True)
    def test_add_data_sample_from_path_with_servermedia_sync_ok(self, *_):
        self._test_add_datasample_from_path_sync_ok()

    @override_settings(ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS=False)
    def test_add_data_sample_from_path_with_minio_sync_ok(self, *_):
        # test upload file to minio from provided path
        self._test_add_datasample_from_path_sync_ok()

    @override_settings(SERVERMEDIAS_ROOT=FIXTURE_PATH)
    def test_bulk_add_data_sample_from_path_sync_ok(self, *_):
        path1 = os.path.join(FIXTURE_PATH, "datasamples/test/0024900")
        path2 = os.path.join(FIXTURE_PATH, "datasamples/test/0024901")

        data = {
            "json": json.dumps(
                {
                    "paths": [path1, path2],
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": True,
                }
            ),
        }
        response = self.client.post(self.url, data, format="multipart", **self.extra)
        r = response.json()
        self.assertEqual(len(r), 2)
        self.assertIsNotNone(r[0]["key"])
        self.assertIsNotNone(r[1]["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_bulk_add_data_sample_sync_ok(self, *_):
        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.read())

        file_mock2 = MagicMock(spec=InMemoryUploadedFile)
        file_mock2.name = "bar.zip"
        file_mock2.read = MagicMock(return_value=self.data_file_2.read())

        data = {
            file_mock.name: file_mock,
            file_mock2.name: file_mock2,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"], self.data_managers[1]["key"]],
                    "test_only": True,
                }
            ),
        }
        self.data_file.seek(0)
        self.data_file_2.seek(0)

        response = self.client.post(self.url, data, format="multipart", **self.extra)
        r = response.json()
        self.assertEqual(len(r), 2)
        self.assertIsNotNone(r[0]["key"])
        self.assertIsNotNone(r[1]["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_validate_servermedias_path(self, *_):
        with override_settings(SERVERMEDIAS_ROOT=FIXTURE_PATH):
            # provided path is not a directory
            path = os.path.join(FIXTURE_PATH, "datasamples/test/0024900/IMG_0024900.jpg")
            data = {
                "json": json.dumps(
                    {
                        "path": path,
                        "data_manager_keys": [self.data_managers[0]["key"]],
                        "test_only": True,
                    }
                ),
            }
            response = self.client.post(self.url, data, format="multipart", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # provided path is not a subpath of servermedias
            path = os.path.join(FIXTURE_PATH, "../chunantes/datasamples/datasample0")
            data = {
                "json": json.dumps(
                    {
                        "path": path,
                        "data_manager_keys": [self.data_managers[0]["key"]],
                        "test_only": True,
                    }
                ),
            }
            response = self.client.post(self.url, data, format="multipart", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # provided path is an empty dir
        with tempfile.TemporaryDirectory() as tmp_path, override_settings(SERVERMEDIAS_ROOT=tmp_path):
            data = {
                "json": json.dumps(
                    {
                        "path": tmp_path,
                        "data_manager_keys": [self.data_managers[0]["key"]],
                        "test_only": True,
                    }
                ),
            }
            response = self.client.post(self.url, data, format="multipart", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # provided path is a symlink
            path = os.path.join(tmp_path, "symlink")
            os.symlink(os.path.join(FIXTURE_PATH, "datasamples/test/0024900"), path)
            data = {
                "json": json.dumps(
                    {
                        "path": path,
                        "data_manager_keys": [self.data_managers[0]["key"]],
                        "test_only": True,
                    }
                ),
            }
            response = self.client.post(self.url, data, format="multipart", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ok_already_exists(self, *_):
        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.file.read())
        file_mock.open = MagicMock(return_value=file_mock)

        d = DataSample(file=File(self.data_file.file), checksum="checksum")
        d.save()

        data = {
            "file": file_mock,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": True,
                }
            ),
        }
        with mock.patch.object(zipfile, "is_zipfile", return_value=True):
            response = self.client.post(self.url, data, format="multipart", **self.extra)
            # it's ok to save duplicate datasamples
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_data_sample_ko_not_a_zip(self, *_):
        file_mock = MagicMock(spec=File)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=b"foo")

        data = {
            "file": file_mock,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": True,
                }
            ),
        }
        response = self.client.post(self.url, data, format="multipart", **self.extra)
        self.assertEqual(
            response.json()["message"], "[ErrorDetail(string='Archive must be zip or tar', code='invalid')]"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_408(self, *_):
        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.file.read())
        file_mock.open = MagicMock(return_value=file_mock)

        data = {
            "file": file_mock,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": True,
                }
            ),
        }
        error = OrcError()
        error.details = "timeout"
        error.code = StatusCode.CANCELLED
        with mock.patch.object(zipfile, "is_zipfile", return_value=True), mock.patch.object(
            OrchestratorClient, "register_datasamples", side_effect=error
        ):
            response = self.client.post(self.url, data, format="multipart", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)

    def test_bulk_add_data_sample_ko_408(self, *_):
        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock2 = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock2.name = "bar.zip"
        file_mock.read = MagicMock(return_value=self.data_file.read())
        file_mock2.read = MagicMock(return_value=self.data_file_2.read())

        data = {
            file_mock.name: file_mock,
            file_mock2.name: file_mock2,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": True,
                }
            ),
        }
        error = OrcError()
        error.details = "timeout"
        error.code = StatusCode.CANCELLED
        with mock.patch(
            "substrapp.serializers.datasample.DataSampleSerializer.get_validators", return_value=[]
        ), mock.patch.object(OrchestratorClient, "register_datasamples", side_effect=error):
            self.data_file.seek(0)
            self.data_tar_file.seek(0)

            response = self.client.post(self.url, data, format="multipart", **self.extra)
            self.assertEqual(DataSample.objects.count(), 0)
            self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)

    def test_bulk_add_data_sample_ok_same_key(self, *_):
        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.read())

        file_mock2 = MagicMock(spec=InMemoryUploadedFile)
        file_mock2.name = "bar.tar.gz"
        file_mock2.read = MagicMock(return_value=self.data_tar_file.read())

        data = {
            file_mock.name: file_mock,
            file_mock2.name: file_mock2,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": True,
                }
            ),
        }
        with mock.patch("substrapp.serializers.datasample.DataSampleSerializer.get_validators", return_value=[]):
            self.data_file.seek(0)
            self.data_tar_file.seek(0)

            response = self.client.post(self.url, data, format="multipart", **self.extra)
            # It's ok to add the same data sample multiple times
            self.assertEqual(DataSample.objects.count(), 2)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_data_sample_ko_400(self, *_):
        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.file.read())

        data = {
            "file": file_mock,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": True,
                }
            ),
        }
        error = OrcError()
        error.details = "Failed"
        error.code = StatusCode.INVALID_ARGUMENT

        with mock.patch.object(zipfile, "is_zipfile", return_value=True), mock.patch.object(
            OrchestratorClient, "register_datasamples", side_effect=error
        ):
            response = self.client.post(self.url, data, format="multipart", **self.extra)
            self.assertEqual(response.json()["message"], "Failed")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_serializer_invalid(self, *_):
        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.read())

        data = {
            "file": file_mock,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_managers[0]["key"]],
                    "test_only": True,
                }
            ),
        }
        mocked_serializer = MagicMock(DataSampleSerializer)
        mocked_serializer.is_valid.return_value = True
        mocked_serializer.save.side_effect = Exception("Failed")
        with mock.patch.object(zipfile, "is_zipfile", return_value=True), mock.patch(
            "substrapp.views.datasample.DataSampleSerializer", return_value=mocked_serializer
        ):
            response = self.client.post(self.url, data, format="multipart", **self.extra)
            self.assertEqual(response.json()["message"], "Failed")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_update_data(self, *_):
        # add associated data opener
        d = DataSample(file=File(self.data_file), checksum="checksum")
        d.save()
        d.key = "ae" * 16  # set key manually otherwise it's empty

        url = reverse("substrapp:data_sample-bulk-update")

        data = {
            "data_manager_keys": [self.data_managers[0]["key"], self.data_managers[1]["key"]],
            "data_sample_keys": [d.key],
        }
        with mock.patch.object(OrchestratorClient, "update_datasample", return_value={"keys": [d.key]}):
            response = self.client.post(url, data, format="json", **self.extra)
            self.assertEqual(response.json()["keys"], [d.key])
            self.assertEqual(response.status_code, status.HTTP_200_OK)

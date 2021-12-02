import json
import os
import shutil
import tempfile
import uuid
import zipfile
from unittest.mock import MagicMock

import mock
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import override_settings
from django.urls import reverse
from grpc import StatusCode
from rest_framework import status
from rest_framework.test import APITestCase

from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from substrapp.models import DataManager
from substrapp.models import DataSample
from substrapp.serializers import DataSampleSerializer
from substrapp.views import DataSampleViewSet

from ..common import AuthenticatedClient
from ..common import get_sample_datamanager
from ..common import get_sample_datamanager2
from ..common import get_sample_script
from ..common import get_sample_tar_data_sample
from ..common import get_sample_zip_data_sample
from ..common import get_sample_zip_data_sample_2

MEDIA_ROOT = tempfile.mkdtemp()
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURE_PATH = os.path.abspath(os.path.join(DIR_PATH, "../../../../fixtures/owkin"))


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
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

        (
            self.data_description,
            self.data_description_filename,
            self.data_data_opener,
            self.data_opener_filename,
        ) = get_sample_datamanager()

        (
            self.data_description2,
            self.data_description_filename2,
            self.data_data_opener2,
            self.data_opener_filename2,
        ) = get_sample_datamanager2()

        self.url = reverse("substrapp:data_sample-list")

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def add_default_data_manager(self):
        dm = DataManager.objects.create(
            name="slide opener", description=self.data_description, data_opener=self.data_data_opener
        )
        self.data_manager_key1 = str(dm.key)

        dm = DataManager.objects.create(
            name="slide opener", description=self.data_description2, data_opener=self.data_data_opener2
        )
        self.data_manager_key2 = str(dm.key)

    def get_default_datasample_data(self):
        self.data_file.file.seek(0)
        data = {
            "file": self.data_file,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }

        return data

    def test_add_data_sample_from_upload_sync_ok(self):

        self.add_default_data_manager()
        data = self.get_default_datasample_data()

        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch.object(OrchestratorClient, "register_datasamples", return_value={}):

            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertIsNotNone(response.json()[0]["key"])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(SERVERMEDIAS_ROOT=FIXTURE_PATH)
    def _test_add_datasample_from_path_sync_ok(self):
        path = os.path.join(FIXTURE_PATH, "datasamples/test/0024900")
        self.add_default_data_manager()

        data = {
            "json": json.dumps(
                {
                    "path": path,
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch.object(OrchestratorClient, "register_datasamples", return_value={}):

            response = self.client.post(self.url, data, format="multipart", **extra)
            jsonr = response.json()
            self.assertIsNotNone(jsonr[0]["key"])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # sensitive data should never be served by the API.
            self.assertNotIn("file", jsonr[0])

    def test_bulk_add_data_sample_ok(self):
        self.add_default_data_manager()

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
                    "data_manager_keys": [self.data_manager_key1, self.data_manager_key2],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch.object(OrchestratorClient, "register_datasamples", return_value={}):

            self.data_file.seek(0)
            self.data_file_2.seek(0)

            response = self.client.post(self.url, data, format="multipart", **extra)
            r = response.json()

            self.assertEqual(len(r), 2)
            self.assertIsNotNone(r[0]["key"])
            self.assertIsNotNone(r[1]["key"])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS=True)
    def test_add_data_sample_from_path_with_servermedia_sync_ok(self):
        self._test_add_datasample_from_path_sync_ok()

    @override_settings(ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS=False)
    def test_add_data_sample_from_path_with_minio_sync_ok(self):
        # test upload file to minio from provided path
        self._test_add_datasample_from_path_sync_ok()

    @override_settings(SERVERMEDIAS_ROOT=FIXTURE_PATH)
    def test_bulk_add_data_sample_from_path_sync_ok(self):
        path1 = os.path.join(FIXTURE_PATH, "datasamples/test/0024900")
        path2 = os.path.join(FIXTURE_PATH, "datasamples/test/0024901")

        self.add_default_data_manager()

        data = {
            "json": json.dumps(
                {
                    "paths": [path1, path2],
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch.object(OrchestratorClient, "register_datasamples", return_value={}):

            response = self.client.post(self.url, data, format="multipart", **extra)
            r = response.json()
            self.assertEqual(len(r), 2)
            self.assertIsNotNone(r[0]["key"])
            self.assertIsNotNone(r[1]["key"])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_bulk_add_data_sample_sync_ok(self):
        self.add_default_data_manager()

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
                    "data_manager_keys": [self.data_manager_key1, self.data_manager_key2],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch.object(OrchestratorClient, "register_datasamples", return_value={}):

            self.data_file.seek(0)
            self.data_file_2.seek(0)

            response = self.client.post(self.url, data, format="multipart", **extra)
            r = response.json()
            self.assertEqual(len(r), 2)
            self.assertIsNotNone(r[0]["key"])
            self.assertIsNotNone(r[1]["key"])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_validate_servermedias_path(self):
        with override_settings(SERVERMEDIAS_ROOT=FIXTURE_PATH):
            # provided path is not a directory
            path = os.path.join(FIXTURE_PATH, "datasamples/test/0024900/IMG_0024900.jpg")
            data = {
                "json": json.dumps(
                    {
                        "path": path,
                        "data_manager_keys": [self.data_manager_key1],
                        "test_only": True,
                    }
                ),
            }
            extra = {
                "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
                "HTTP_ACCEPT": "application/json;version=0.0",
            }
            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # provided path is not a subpath of servermedias
            path = os.path.join(FIXTURE_PATH, "../chunantes/datasamples/datasample0")
            data = {
                "json": json.dumps(
                    {
                        "path": path,
                        "data_manager_keys": [self.data_manager_key1],
                        "test_only": True,
                    }
                ),
            }
            extra = {
                "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
                "HTTP_ACCEPT": "application/json;version=0.0",
            }
            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # provided path is an empty dir
        with tempfile.TemporaryDirectory() as tmp_path, override_settings(SERVERMEDIAS_ROOT=tmp_path):
            data = {
                "json": json.dumps(
                    {
                        "path": tmp_path,
                        "data_manager_keys": [self.data_manager_key1],
                        "test_only": True,
                    }
                ),
            }
            extra = {
                "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
                "HTTP_ACCEPT": "application/json;version=0.0",
            }
            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # provided path is a symlink
            path = os.path.join(tmp_path, "symlink")
            os.symlink(os.path.join(FIXTURE_PATH, "datasamples/test/0024900"), path)
            data = {
                "json": json.dumps(
                    {
                        "path": path,
                        "data_manager_keys": [self.data_manager_key1],
                        "test_only": True,
                    }
                ),
            }
            extra = {
                "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
                "HTTP_ACCEPT": "application/json;version=0.0",
            }
            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko(self):
        # missing datamanager
        data = {"data_manager_keys": [str(uuid.uuid4())]}
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        response = self.client.post(self.url, data, format="json", **extra)
        self.assertEqual(
            response.json()["message"],
            "One or more datamanager keys provided do not exist in local database. "
            "Please create them before. DataManager keys: ['"
            f"{data['data_manager_keys'][0]}"
            "']",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.add_default_data_manager()

        # missing local storage field
        data = {
            "data_manager_keys": [self.data_manager_key1],
            "test_only": True,
        }
        response = self.client.post(self.url, data, format="multipart", **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # missing orchestrator field
        data = {
            "data_manager_keys": [self.data_manager_key1],
            "file": self.script,
        }
        response = self.client.post(self.url, data, format="multipart", **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ok_already_exists(self):
        self.add_default_data_manager()

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
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch.object(zipfile, "is_zipfile", return_value=True), mock.patch.object(
            OrchestratorClient, "register_datasamples", return_value={}
        ):

            response = self.client.post(self.url, data, format="multipart", **extra)
            # it's ok to save duplicate datasamples
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_data_sample_ko_not_a_zip(self):

        self.add_default_data_manager()
        file_mock = MagicMock(spec=File)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=b"foo")

        data = {
            "file": file_mock,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        response = self.client.post(self.url, data, format="multipart", **extra)
        self.assertEqual(
            response.json()["message"], "[ErrorDetail(string='Archive must be zip or tar', code='invalid')]"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_408(self):

        self.add_default_data_manager()

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.file.read())
        file_mock.open = MagicMock(return_value=file_mock)

        data = {
            "file": file_mock,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        error = OrcError()
        error.details = "timeout"
        error.code = StatusCode.CANCELLED
        with mock.patch.object(zipfile, "is_zipfile", return_value=True), mock.patch.object(
            OrchestratorClient, "register_datasamples", side_effect=error
        ):
            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)

    def test_bulk_add_data_sample_ko_408(self):

        self.add_default_data_manager()

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
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        error = OrcError()
        error.details = "timeout"
        error.code = StatusCode.CANCELLED
        with mock.patch(
            "substrapp.serializers.datasample.DataSampleSerializer.get_validators", return_value=[]
        ), mock.patch.object(OrchestratorClient, "register_datasamples", side_effect=error):
            self.data_file.seek(0)
            self.data_tar_file.seek(0)

            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertEqual(DataSample.objects.count(), 0)
            self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)

    def test_bulk_add_data_sample_ok_same_key(self):

        self.add_default_data_manager()

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
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch(
            "substrapp.serializers.datasample.DataSampleSerializer.get_validators", return_value=[]
        ), mock.patch.object(OrchestratorClient, "register_datasamples", return_value={}):
            self.data_file.seek(0)
            self.data_tar_file.seek(0)

            response = self.client.post(self.url, data, format="multipart", **extra)
            # It's ok to add the same data sample multiple times
            self.assertEqual(DataSample.objects.count(), 2)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_data_sample_ko_400(self):
        url = reverse("substrapp:data_sample-list")

        self.add_default_data_manager()

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.file.read())

        data = {
            "file": file_mock,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        error = OrcError()
        error.details = "Failed"
        error.code = StatusCode.INVALID_ARGUMENT

        with mock.patch.object(zipfile, "is_zipfile", return_value=True), mock.patch.object(
            OrchestratorClient, "register_datasamples", side_effect=error
        ):
            response = self.client.post(url, data, format="multipart", **extra)
            self.assertEqual(response.json()["message"], "Failed")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_serializer_invalid(self):
        self.add_default_data_manager()

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.read())

        data = {
            "file": file_mock,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        mocked_serializer = MagicMock(DataSampleSerializer)
        mocked_serializer.is_valid.return_value = True
        mocked_serializer.save.side_effect = Exception("Failed")
        with mock.patch.object(zipfile, "is_zipfile", return_value=True), mock.patch.object(
            DataSampleViewSet, "get_serializer", return_value=mocked_serializer
        ):

            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertEqual(response.json()["message"], "Failed")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_data_sample_ko_orchestrator_invalid(self):
        self.add_default_data_manager()

        file_mock = MagicMock(spec=InMemoryUploadedFile)
        file_mock.name = "foo.zip"
        file_mock.read = MagicMock(return_value=self.data_file.file.read())

        data = {
            "file": file_mock,
            "json": json.dumps(
                {
                    "data_manager_keys": [self.data_manager_key1],
                    "test_only": True,
                }
            ),
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        mocked_OrchestratorDataSampleSerializer = MagicMock()  # noqa: N806
        mocked_OrchestratorDataSampleSerializer.is_valid.return_value = False
        mocked_OrchestratorDataSampleSerializer.errors = "Failed"
        with mock.patch.object(zipfile, "is_zipfile", return_value=True), mock.patch(
            "substrapp.views.datasample.OrchestratorDataSampleSerializer",
            return_value=mocked_OrchestratorDataSampleSerializer,
        ):

            response = self.client.post(self.url, data, format="multipart", **extra)
            self.assertEqual(response.json()["message"], "[ErrorDetail(string='Failed', code='invalid')]")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_update_data(self):

        # add associated data opener
        datamanager = DataManager.objects.create(
            name="slide opener", description=self.data_description, data_opener=self.data_data_opener
        )
        datamanager2 = DataManager.objects.create(
            name="slide opener 2", description=self.data_description2, data_opener=self.data_data_opener2
        )
        d = DataSample(file=File(self.data_file), checksum="checksum")
        d.save()
        d.key = "ae" * 16  # set key manually otherwise it's empty

        url = reverse("substrapp:data_sample-bulk-update")

        data = {
            "data_manager_keys": [datamanager.key, datamanager2.key],
            "data_sample_keys": [d.key],
        }
        extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

        with mock.patch.object(OrchestratorClient, "update_datasample", return_value={"keys": [d.key]}):

            response = self.client.post(url, data, format="json", **extra)
            self.assertEqual(response.json()["keys"], [d.key])
            self.assertEqual(response.status_code, status.HTTP_200_OK)

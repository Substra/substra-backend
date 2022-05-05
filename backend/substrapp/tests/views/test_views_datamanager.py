import json
import logging
import os
import shutil
import tempfile
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from grpc import StatusCode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from localrep.models import DataManager as DataManagerRep
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from substrapp.tests import factory

from ..common import AuthenticatedClient
from ..common import internal_server_error_on_exception

MEDIA_ROOT = tempfile.mkdtemp()

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURE_PATH = os.path.join(DIR_PATH, "../../../../fixtures/chunantes/datamanagers/datamanager0")


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    LEDGER_MSP_ID="MyTestOrg",
)
class DataManagerViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.url = reverse("substrapp:data_manager-list")
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

        data_manager_1 = factory.create_datamanager(name="datamanager foo")
        train_data_sample = factory.create_datasample([data_manager_1])
        test_data_sample = factory.create_datasample([data_manager_1], test_only=True)
        # only for retrieve view
        self.train_data_sample_keys = [str(train_data_sample.key)]
        self.test_data_sample_keys = [str(test_data_sample.key)]

        data_manager_2 = factory.create_datamanager()
        data_manager_3 = factory.create_datamanager()
        self.expected_results = [
            {
                "key": str(data_manager_1.key),
                "name": "datamanager foo",
                "owner": "MyOrg1MSP",
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                    "download": {
                        "public": False,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                },
                "type": "Test",
                "opener": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/data_manager/{data_manager_1.key}/opener/",
                },
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/data_manager/{data_manager_1.key}/description/",
                },
                "metadata": {},
                "creation_date": data_manager_1.creation_date.isoformat().replace("+00:00", "Z"),
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
            {
                "key": str(data_manager_2.key),
                "name": "datamanager",
                "owner": "MyOrg1MSP",
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                    "download": {
                        "public": False,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                },
                "type": "Test",
                "opener": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/data_manager/{data_manager_2.key}/opener/",
                },
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/data_manager/{data_manager_2.key}/description/",
                },
                "metadata": {},
                "creation_date": data_manager_2.creation_date.isoformat().replace("+00:00", "Z"),
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
            {
                "key": str(data_manager_3.key),
                "name": "datamanager",
                "owner": "MyOrg1MSP",
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                    "download": {
                        "public": False,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                },
                "type": "Test",
                "opener": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/data_manager/{data_manager_3.key}/opener/",
                },
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/data_manager/{data_manager_3.key}/description/",
                },
                "metadata": {},
                "creation_date": data_manager_3.creation_date.isoformat().replace("+00:00", "Z"),
                "logs_permission": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
        ]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    def test_datamanager_list_empty(self):
        DataManagerRep.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_datamanager_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_datamanager_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.datamanager.DataManagerViewSet.list", side_effect=Exception("Unexpected error"))
    def test_datamanager_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_datamanager_list_storage_addresses_update(self):
        for data_manager in DataManagerRep.objects.all():
            data_manager.description_address.replace("http://testserver", "http://remotetestserver")
            data_manager.opener_address.replace("http://testserver", "http://remotetestserver")
            data_manager.save()

        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.data["count"], len(self.expected_results))
        for result, data_manager in zip(response.data["results"], self.expected_results):
            for field in ("description", "opener"):
                self.assertEqual(result[field]["storage_address"], data_manager[field]["storage_address"])

    def test_datamanager_list_search_filter(self):
        """Filter datamanager on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"search": f"dataset:key:{key}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_datamanager_list_filter(self):
        """Filter datamanager on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_datamanager_list_search_filter_and(self):
        """Filter datamanager on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"search": f"dataset:key:{key},dataset:owner:{owner}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_datamanager_list_filter_and(self):
        """Filter datamanager on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"key": key, "owner": owner})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_datamanager_list_search_filter_in(self):
        """Filter datamanager in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"search": f"dataset:key:{key_0},dataset:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_datamanager_list_filter_in(self):
        """Filter datamanager in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_datamanager_list_search_filter_or(self):
        """Filter datamanager on key_0 or key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"search": f"dataset:key:{key_0}-OR-dataset:key:{key_1}"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_datamanager_list_search_filter_or_and(self):
        """Filter datamanager on (key_0 and owner_0) or (key_1 and owner_1)."""
        key_0, owner_0 = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        key_1, owner_1 = self.expected_results[1]["key"], self.expected_results[1]["owner"]
        params = urlencode(
            {
                "search": (
                    f"dataset:key:{key_0},dataset:owner:{owner_0}" f"-OR-dataset:key:{key_1},dataset:owner:{owner_1}"
                )
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    def test_datamanager_match(self):
        """Match datamanager on part of the name."""
        params = urlencode({"match": "manager fo"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_datamanager_match_and_search_filter(self):
        """Match datamanager with filter."""
        params = urlencode(
            {
                "search": f"dataset:key:{self.expected_results[0]['key']}",
                "match": "manager fo",
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_datamanager_match_and_filter(self):
        """Match datamanager with filter."""
        params = urlencode(
            {
                "key": self.expected_results[0]["key"],
                "match": "manager fo",
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    @parameterized.expand(
        [
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_datamanager_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_datamanager_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results[::-1]),

    def test_datamanager_create(self):
        def mock_orc_response(data):
            """Build orchestrator register response from request data."""
            return {
                "key": data["key"],
                "name": data["name"],
                "type": data["type"],
                "owner": data["new_permissions"]["authorized_ids"][0],
                "permissions": {
                    "process": data["new_permissions"],
                    "download": data["new_permissions"],
                },
                "logs_permission": data["logs_permission"],
                "metadata": {},
                "creation_date": "2021-11-04T13:54:09.882662Z",
                "description": data["description"],
                "opener": data["opener"],
            }

        opener_path = os.path.join(FIXTURE_PATH, "opener.py")
        description_path = os.path.join(FIXTURE_PATH, "description.md")
        data = {
            "json": json.dumps(
                {
                    "name": "Datamanager test",
                    "type": "Test",
                    "permissions": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                    "logs_permission": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                }
            ),
            "data_opener": open(opener_path, "rb"),
            "description": open(description_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_datamanager", side_effect=mock_orc_response):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        self.assertIsNotNone(response.data["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # asset created in local db
        self.assertEqual(DataManagerRep.objects.count(), len(self.expected_results) + 1)

        data["data_opener"].close()
        data["description"].close()

    @override_settings(DATA_UPLOAD_MAX_SIZE=150)
    def test_file_size_limit(self):
        opener_path = os.path.join(FIXTURE_PATH, "opener.py")
        description_path = os.path.join(FIXTURE_PATH, "description.md")
        data = {
            "json": json.dumps(
                {
                    "name": "Datamanager test",
                    "type": "Test",
                    "permissions": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                    "logs_permission": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                }
            ),
            "data_opener": open(opener_path, "rb"),
            "description": open(description_path, "rb"),
        }

        response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File too large", response.data["message"][0]["data_opener"])

        data["data_opener"].close()
        data["description"].close()

    def test_datamanager_create_fail_rollback(self):
        class MockOrcError(OrcError):
            code = StatusCode.ALREADY_EXISTS
            details = "already exists"

        opener_path = os.path.join(FIXTURE_PATH, "opener.py")
        description_path = os.path.join(FIXTURE_PATH, "description.md")
        data = {
            "json": json.dumps(
                {
                    "name": "Datamanager test",
                    "type": "Test",
                    "permissions": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                    "logs_permission": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                }
            ),
            "data_opener": open(opener_path, "rb"),
            "description": open(description_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_datamanager", side_effect=MockOrcError()):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        # asset not created in local db
        self.assertEqual(DataManagerRep.objects.count(), len(self.expected_results))
        # orc error code should be propagated
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        data["data_opener"].close()
        data["description"].close()

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.datamanager.DataManagerViewSet.create", side_effect=Exception("Unexpected error"))
    def test_datamanager_create_fail(self, _):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_datamanager_retrieve(self):
        self.expected_results[0]["train_data_sample_keys"] = self.train_data_sample_keys
        self.expected_results[0]["test_data_sample_keys"] = self.test_data_sample_keys
        url = reverse("substrapp:data_manager-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.expected_results[0])

    def test_datamanager_retrieve_wrong_channel(self):
        url = reverse("substrapp:data_manager-detail", args=[self.expected_results[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_datamanager_retrieve_storage_addresses_update(self):
        data_manager = DataManagerRep.objects.get(key=self.expected_results[0]["key"])
        data_manager.description_address.replace("http://testserver", "http://remotetestserver")
        data_manager.opener_address.replace("http://testserver", "http://remotetestserver")
        data_manager.save()

        url = reverse("substrapp:data_manager-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        for field in ("description", "opener"):
            self.assertEqual(
                response.data[field]["storage_address"], self.expected_results[0][field]["storage_address"]
            )

    @internal_server_error_on_exception()
    @mock.patch("substrapp.views.datamanager.DataManagerViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_datamanager_retrieve_fail(self, _):
        url = reverse("substrapp:data_manager-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

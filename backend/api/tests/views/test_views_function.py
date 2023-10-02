import json
import logging
import os
import shutil
import tempfile
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Function
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient
from api.tests.common import internal_server_error_on_exception
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from orchestrator.error import StatusCode
from substrapp.tests.common import FunctionCategory
from substrapp.utils import compute_hash

MEDIA_ROOT = tempfile.mkdtemp()

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURE_PATH = os.path.join(DIR_PATH, "../../../../fixtures/chunantes/functions/function0")


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    CHANNELS={"mychannel": {"model_export_enabled": True}},
)
class FunctionViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)
        self.url = reverse("api:function-list")

        simple_function = factory.create_function(
            inputs=factory.build_function_inputs(["datasamples", "opener", "model"]),
            outputs=factory.build_function_outputs(["model"]),
            name="simple function",
        )
        aggregate_function = factory.create_function(
            inputs=factory.build_function_inputs(["models"]),
            outputs=factory.build_function_outputs(["model"]),
            name="aggregate",
        )
        composite_function = factory.create_function(
            inputs=factory.build_function_inputs(["datasamples", "opener", "local", "shared"]),
            outputs=factory.build_function_outputs(["local", "shared"]),
            name="composite",
        )
        predict_function = factory.create_function(
            inputs=factory.build_function_inputs(["datasamples", "opener", "model", "shared"]),
            outputs=factory.build_function_outputs(["predictions"]),
            name="predict",
        )
        metric_function = factory.create_function(
            inputs=factory.build_function_inputs(["datasamples", "opener", "predictions"]),
            outputs=factory.build_function_outputs(["performance"]),
            name="metric",
        )

        self.functions = [simple_function, aggregate_function, composite_function, predict_function]
        self.expected_functions = [
            {
                "key": str(simple_function.key),
                "name": "simple function",
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
                "metadata": {},
                "creation_date": simple_function.creation_date.isoformat().replace("+00:00", "Z"),
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/function/{simple_function.key}/description/",
                },
                "function": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/function/{simple_function.key}/file/",
                },
                "inputs": {
                    "datasamples": {"kind": "ASSET_DATA_SAMPLE", "optional": False, "multiple": True},
                    "opener": {"kind": "ASSET_DATA_MANAGER", "optional": False, "multiple": False},
                    "model": {"kind": "ASSET_MODEL", "optional": True, "multiple": False},
                },
                "outputs": {
                    "model": {"kind": "ASSET_MODEL", "multiple": False},
                },
                "status": "FUNCTION_STATUS_WAITING",
            },
            {
                "key": str(aggregate_function.key),
                "name": "aggregate",
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
                "metadata": {},
                "creation_date": aggregate_function.creation_date.isoformat().replace("+00:00", "Z"),
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/function/{aggregate_function.key}/description/",
                },
                "function": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/function/{aggregate_function.key}/file/",
                },
                "inputs": {
                    "models": {"kind": "ASSET_MODEL", "optional": True, "multiple": True},
                },
                "outputs": {
                    "model": {"kind": "ASSET_MODEL", "multiple": False},
                },
                "status": "FUNCTION_STATUS_WAITING",
            },
            {
                "key": str(composite_function.key),
                "name": "composite",
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
                "metadata": {},
                "creation_date": composite_function.creation_date.isoformat().replace("+00:00", "Z"),
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/function/{composite_function.key}/description/",
                },
                "function": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/function/{composite_function.key}/file/",
                },
                "inputs": {
                    "datasamples": {"kind": "ASSET_DATA_SAMPLE", "optional": False, "multiple": True},
                    "opener": {"kind": "ASSET_DATA_MANAGER", "optional": False, "multiple": False},
                    "local": {"kind": "ASSET_MODEL", "optional": True, "multiple": False},
                    "shared": {"kind": "ASSET_MODEL", "optional": True, "multiple": False},
                },
                "outputs": {
                    "local": {"kind": "ASSET_MODEL", "multiple": False},
                    "shared": {"kind": "ASSET_MODEL", "multiple": False},
                },
                "status": "FUNCTION_STATUS_WAITING",
            },
            {
                "key": str(predict_function.key),
                "name": "predict",
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
                "metadata": {},
                "creation_date": predict_function.creation_date.isoformat().replace("+00:00", "Z"),
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/function/{predict_function.key}/description/",
                },
                "function": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/function/{predict_function.key}/file/",
                },
                "inputs": {
                    "datasamples": {"kind": "ASSET_DATA_SAMPLE", "optional": False, "multiple": True},
                    "opener": {"kind": "ASSET_DATA_MANAGER", "optional": False, "multiple": False},
                    "model": {"kind": "ASSET_MODEL", "optional": True, "multiple": False},
                    "shared": {"kind": "ASSET_MODEL", "optional": True, "multiple": False},
                },
                "outputs": {
                    "predictions": {"kind": "ASSET_MODEL", "multiple": False},
                },
                "status": "FUNCTION_STATUS_WAITING",
            },
            {
                "key": str(metric_function.key),
                "name": "metric",
                "owner": "MyOrg1MSP",
                "metadata": {},
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
                "creation_date": metric_function.creation_date.isoformat().replace("+00:00", "Z"),
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/function/{metric_function.key}/description/",
                },
                "function": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/function/{metric_function.key}/file/",
                },
                "inputs": {
                    "datasamples": {"kind": "ASSET_DATA_SAMPLE", "optional": False, "multiple": True},
                    "opener": {"kind": "ASSET_DATA_MANAGER", "optional": False, "multiple": False},
                    "predictions": {"kind": "ASSET_MODEL", "optional": False, "multiple": False},
                },
                "outputs": {
                    "performance": {"kind": "ASSET_PERFORMANCE", "multiple": False},
                },
                "status": "FUNCTION_STATUS_WAITING",
            },
        ]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    def test_function_list_empty(self):
        Function.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_function_list_success(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response.json(),
            {
                "count": len(self.expected_functions),
                "next": None,
                "previous": None,
                "results": self.expected_functions,
            },
        )

    def test_function_list_wrong_channel(self):
        self.client.channel = "yourchannel"
        response = self.client.get(self.url)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("api.views.function.FunctionViewSet.list", side_effect=Exception("Unexpected error"))
    def test_function_list_fail(self, _):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_function_list_storage_addresses_update(self):
        for function in Function.objects.all():
            function.description_address.replace("http://testserver", "http://remotetestserver")
            function.archive_address.replace("http://testserver", "http://remotetestserver")
            function.save()

        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], len(self.expected_functions))
        for result, function in zip(response.data["results"], self.expected_functions):
            for field in ("description", "function"):
                self.assertEqual(result[field]["storage_address"], function[field]["storage_address"])

    def test_function_list_filter(self):
        """Filter function on key."""
        key = self.expected_functions[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_functions[:1]}
        )

    def test_function_list_filter_and(self):
        """Filter function on key and owner."""
        key, owner = self.expected_functions[0]["key"], self.expected_functions[0]["owner"]
        params = urlencode({"key": key, "owner": owner})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_functions[:1]}
        )

    def test_function_list_filter_in(self):
        """Filter function in key_0, key_1."""
        key_0 = self.expected_functions[0]["key"]
        key_1 = self.expected_functions[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_functions[:2]}
        )

    def test_function_match(self):
        """Match function on part of the name."""
        params = urlencode({"match": "le fu"})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_functions[:1]}
        )

    def test_function_match_and_filter(self):
        """Match function with filter."""
        params = urlencode(
            {
                "key": self.expected_functions[0]["key"],
                "match": "le fu",
            }
        )
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_functions[:1]}
        )

    def test_function_list_compute_plan_key_filter(self):
        """Filter functions on compute_plan_key"""
        compute_plan = factory.create_computeplan()

        factory.create_computetask(compute_plan, self.functions[0])
        factory.create_computetask(compute_plan, self.functions[1])

        # filter on compute_plan_key
        params = urlencode({"compute_plan_key": compute_plan.key})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(response.json().get("results"), self.expected_functions[:2])

    def test_function_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(response.json().get("results"), self.expected_functions),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(response.json().get("results"), self.expected_functions[::-1]),

    @parameterized.expand(
        [
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_function_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}")
        r = response.json()
        self.assertEqual(r["count"], len(self.expected_functions))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_functions[offset : offset + page_size])

    def test_function_cp_list_success(self):
        """List functions for a specific compute plan (CPFunctionViewSet)."""

        compute_plan = factory.create_computeplan()
        factory.create_computetask(compute_plan, self.functions[0])
        factory.create_computetask(compute_plan, self.functions[1])

        url = reverse("api:compute_plan_function-list", args=[compute_plan.key])
        response = self.client.get(url)
        self.assertEqual(
            response.json(),
            {
                "count": len(self.expected_functions[:2]),
                "next": None,
                "previous": None,
                "results": self.expected_functions[:2],
            },
        )

    def test_function_list_can_process(self):
        public_function = Function.objects.get(key=self.expected_functions[0]["key"])
        public_function.permissions_process_public = True
        public_function.save()
        self.expected_functions[0]["permissions"]["process"]["public"] = True

        shared_function = Function.objects.get(key=self.expected_functions[1]["key"])
        shared_function.permissions_process_authorized_ids = ["MyOrg1MSP", "MyOrg2MSP"]
        shared_function.save()
        self.expected_functions[1]["permissions"]["process"]["authorized_ids"] = ["MyOrg1MSP", "MyOrg2MSP"]

        params = urlencode({"can_process": "MyOrg1MSP"})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(response.json().get("results"), self.expected_functions),

        params = urlencode({"can_process": "MyOrg2MSP"})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(response.json().get("results"), self.expected_functions[:2]),

        params = urlencode({"can_process": "MyOrg3MSP"})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(response.json().get("results"), [self.expected_functions[0]]),

        params = urlencode({"can_process": "MyOrg1MSP,MyOrg2MSP"})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(response.json().get("results"), self.expected_functions[:2]),

    @parameterized.expand(
        [
            (category, filename)
            for category in [
                FunctionCategory.simple,
                FunctionCategory.aggregate,
                FunctionCategory.composite,
                FunctionCategory.metric,
                FunctionCategory.predict,
            ]
            for filename in [
                "function.tar.gz",
                "function.zip",
            ]
        ]
    )
    def test_function_create(self, category, filename):
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
                "function": data["function"],
                "inputs": data["inputs"],
                "outputs": data["outputs"],
                "status": Function.Status.FUNCTION_STATUS_WAITING,
            }

        function_path = os.path.join(FIXTURE_PATH, filename)
        description_path = os.path.join(FIXTURE_PATH, "description.md")
        data = {
            "json": json.dumps(
                {
                    "name": "Logistic regression",
                    "metric_key": "some key",
                    "permissions": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                    "inputs": {
                        "datasamples": {"kind": "ASSET_DATA_SAMPLE", "optional": False, "multiple": True},
                        "opener": {"kind": "ASSET_DATA_MANAGER", "optional": False, "multiple": False},
                        "model": {"kind": "ASSET_MODEL", "optional": True, "multiple": False},
                    },
                    "outputs": {
                        "model": {"kind": "ASSET_MODEL", "multiple": False},
                    },
                }
            ),
            "file": open(function_path, "rb"),
            "description": open(description_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_function", side_effect=mock_orc_response):
            response = self.client.post(self.url, data=data, format="multipart")
        self.assertIsNotNone(response.data["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # asset created in local db
        self.assertEqual(Function.objects.count(), len(self.expected_functions) + 1)

        data["file"].close()
        data["description"].close()

    @override_settings(DATA_UPLOAD_MAX_SIZE=150)
    def test_file_size_limit(self):
        function_path = os.path.join(FIXTURE_PATH, "function.tar.gz")
        description_path = os.path.join(FIXTURE_PATH, "description.md")

        data = {
            "json": json.dumps(
                {
                    "name": "Logistic regression",
                    "metric_key": "some key",
                    "permissions": {
                        "public": True,
                        "authorized_ids": ["MyOrg1MSP"],
                    },
                    "inputs": {
                        "datasamples": {"kind": "ASSET_DATA_SAMPLE", "optional": False, "multiple": True},
                        "opener": {"kind": "ASSET_DATA_MANAGER", "optional": False, "multiple": False},
                        "model": {"kind": "ASSET_MODEL", "optional": True, "multiple": False},
                    },
                    "outputs": {
                        "model": {"kind": "ASSET_MODEL", "multiple": False},
                    },
                }
            ),
            "file": open(function_path, "rb"),
            "description": open(description_path, "rb"),
        }

        response = self.client.post(self.url, data=data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File too large", response.data["detail"][0]["file"])

        data["description"].close()
        data["file"].close()

    def test_function_create_fail_rollback(self):
        class MockOrcError(OrcError):
            def __init__(self) -> None:
                pass

            code = StatusCode.ALREADY_EXISTS
            details = "already exists"

        function_path = os.path.join(FIXTURE_PATH, "function.tar.gz")
        description_path = os.path.join(FIXTURE_PATH, "description.md")
        data = {
            "json": json.dumps(
                {
                    "name": "Logistic regression",
                    "metric_key": "some key",
                    "permissions": {
                        "public": True,
                        "authorized_ids": [],
                    },
                    "inputs": {
                        "datasamples": {"kind": "ASSET_DATA_SAMPLE", "optional": False, "multiple": True},
                        "opener": {"kind": "ASSET_DATA_MANAGER", "optional": False, "multiple": False},
                        "model": {"kind": "ASSET_MODEL", "optional": True, "multiple": False},
                    },
                    "outputs": {
                        "model": {"kind": "ASSET_MODEL", "multiple": False},
                    },
                }
            ),
            "file": open(function_path, "rb"),
            "description": open(description_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_function", side_effect=MockOrcError()):
            response = self.client.post(self.url, data=data, format="multipart")
        # asset not created in local db
        self.assertEqual(Function.objects.count(), len(self.expected_functions))
        # orc error code should be propagated
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    @internal_server_error_on_exception()
    @mock.patch("api.views.function.FunctionViewSet.create", side_effect=Exception("Unexpected error"))
    def test_function_create_fail(self, _):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_function_retrieve(self):
        url = reverse("api:function-detail", args=[self.expected_functions[0]["key"]])
        response = self.client.get(url)
        self.assertEqual(response.json(), self.expected_functions[0])

    def test_function_retrieve_wrong_channel(self):
        url = reverse("api:function-detail", args=[self.expected_functions[0]["key"]])
        self.client.channel = "yourchannel"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_function_retrieve_storage_addresses_update(self):
        function = Function.objects.get(key=self.expected_functions[0]["key"])
        function.description_address.replace("http://testserver", "http://remotetestserver")
        function.archive_address.replace("http://testserver", "http://remotetestserver")
        function.save()

        url = reverse("api:function-detail", args=[self.expected_functions[0]["key"]])
        response = self.client.get(url)
        for field in ("description", "function"):
            self.assertEqual(
                response.data[field]["storage_address"], self.expected_functions[0][field]["storage_address"]
            )

    @internal_server_error_on_exception()
    @mock.patch("api.views.function.FunctionViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_function_retrieve_fail(self, _):
        url = reverse("api:function-detail", args=[self.expected_functions[0]["key"]])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_function_download_file(self):
        function_files = factory.create_function_files()
        function = factory.create_function(key=function_files.key)
        url = reverse("api:function-file", args=[function.key])
        with mock.patch("api.views.utils.get_owner", return_value=function.owner):
            response = self.client.get(url)
        content = response.getvalue()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content, function_files.file.read())
        self.assertEqual(compute_hash(content), function_files.checksum)

    def test_function_download_description(self):
        function_files = factory.create_function_files()
        function = factory.create_function(key=function_files.key)
        url = reverse("api:function-description", args=[function.key])
        with mock.patch("api.views.utils.get_owner", return_value=function.owner):
            response = self.client.get(url)
        content = response.getvalue()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content, function_files.description.read())

    def test_function_update(self):
        function = self.expected_functions[0]
        data = {
            "key": function["key"],
            "name": "Bar",
        }

        url = reverse("api:function-detail", args=[function["key"]])
        function["name"] = data["name"]

        with mock.patch.object(OrchestratorClient, "update_function", side_effect=function):
            response = self.client.put(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        error = OrcError()
        error.code = StatusCode.INTERNAL

        with mock.patch.object(OrchestratorClient, "update_function", side_effect=error):
            response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

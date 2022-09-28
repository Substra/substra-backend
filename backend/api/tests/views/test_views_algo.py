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

from api.models import Algo
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient
from api.tests.common import internal_server_error_on_exception
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from orchestrator.error import StatusCode
from substrapp.tests.common import AlgoCategory
from substrapp.utils import compute_hash

MEDIA_ROOT = tempfile.mkdtemp()

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURE_PATH = os.path.join(DIR_PATH, "../../../../fixtures/chunantes/algos/algo0")


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class AlgoViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)
        self.url = reverse("api:algo-list")

        simple_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "model"]),
            outputs=factory.build_algo_outputs(["model"]),
            name="simple algo",
        )
        aggregate_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["model"]),
            outputs=factory.build_algo_outputs(["model"]),
            name="aggregate",
        )
        composite_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "local", "shared"]),
            outputs=factory.build_algo_outputs(["local", "shared"]),
            name="composite",
        )
        predict_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "model", "shared"]),
            outputs=factory.build_algo_outputs(["predictions"]),
            name="predict",
        )
        metric_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "predictions"]),
            outputs=factory.build_algo_outputs(["performance"]),
            name="metric",
        )

        self.algos = [simple_algo, aggregate_algo, composite_algo, predict_algo]
        self.expected_algos = [
            {
                "key": str(simple_algo.key),
                "name": "simple algo",
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
                "creation_date": simple_algo.creation_date.isoformat().replace("+00:00", "Z"),
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/algo/{simple_algo.key}/description/",
                },
                "algorithm": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/algo/{simple_algo.key}/file/",
                },
                "inputs": {
                    "datasamples": {"kind": "ASSET_DATA_SAMPLE", "optional": False, "multiple": True},
                    "opener": {"kind": "ASSET_DATA_MANAGER", "optional": False, "multiple": False},
                    "model": {"kind": "ASSET_MODEL", "optional": True, "multiple": False},
                },
                "outputs": {
                    "model": {"kind": "ASSET_MODEL", "multiple": False},
                },
            },
            {
                "key": str(aggregate_algo.key),
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
                "creation_date": aggregate_algo.creation_date.isoformat().replace("+00:00", "Z"),
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/algo/{aggregate_algo.key}/description/",
                },
                "algorithm": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/algo/{aggregate_algo.key}/file/",
                },
                "inputs": {
                    "model": {"kind": "ASSET_MODEL", "optional": True, "multiple": False},
                },
                "outputs": {
                    "model": {"kind": "ASSET_MODEL", "multiple": False},
                },
            },
            {
                "key": str(composite_algo.key),
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
                "creation_date": composite_algo.creation_date.isoformat().replace("+00:00", "Z"),
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/algo/{composite_algo.key}/description/",
                },
                "algorithm": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/algo/{composite_algo.key}/file/",
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
            },
            {
                "key": str(predict_algo.key),
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
                "creation_date": predict_algo.creation_date.isoformat().replace("+00:00", "Z"),
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/algo/{predict_algo.key}/description/",
                },
                "algorithm": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/algo/{predict_algo.key}/file/",
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
            },
            {
                "key": str(metric_algo.key),
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
                "creation_date": metric_algo.creation_date.isoformat().replace("+00:00", "Z"),
                "description": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/algo/{metric_algo.key}/description/",
                },
                "algorithm": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/algo/{metric_algo.key}/file/",
                },
                "inputs": {
                    "datasamples": {"kind": "ASSET_DATA_SAMPLE", "optional": False, "multiple": True},
                    "opener": {"kind": "ASSET_DATA_MANAGER", "optional": False, "multiple": False},
                    "predictions": {"kind": "ASSET_MODEL", "optional": False, "multiple": False},
                },
                "outputs": {
                    "performance": {"kind": "ASSET_PERFORMANCE", "multiple": False},
                },
            },
        ]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    def test_algo_list_empty(self):
        Algo.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_algo_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {
                "count": len(self.expected_algos),
                "next": None,
                "previous": None,
                "results": self.expected_algos,
            },
        )

    def test_algo_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("api.views.algo.AlgoViewSet.list", side_effect=Exception("Unexpected error"))
    def test_algo_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_algo_list_storage_addresses_update(self):
        for algo in Algo.objects.all():
            algo.description_address.replace("http://testserver", "http://remotetestserver")
            algo.algorithm_address.replace("http://testserver", "http://remotetestserver")
            algo.save()

        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.data["count"], len(self.expected_algos))
        for result, algo in zip(response.data["results"], self.expected_algos):
            for field in ("description", "algorithm"):
                self.assertEqual(result[field]["storage_address"], algo[field]["storage_address"])

    def test_algo_list_filter(self):
        """Filter algo on key."""
        key = self.expected_algos[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_algos[:1]}
        )

    def test_algo_list_filter_and(self):
        """Filter algo on key and owner."""
        key, owner = self.expected_algos[0]["key"], self.expected_algos[0]["owner"]
        params = urlencode({"key": key, "owner": owner})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_algos[:1]}
        )

    def test_algo_list_filter_in(self):
        """Filter algo in key_0, key_1."""
        key_0 = self.expected_algos[0]["key"]
        key_1 = self.expected_algos[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_algos[:2]}
        )

    def test_algo_match(self):
        """Match algo on part of the name."""
        params = urlencode({"match": "le al"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_algos[:1]}
        )

    def test_algo_match_and_filter(self):
        """Match algo with filter."""
        params = urlencode(
            {
                "key": self.expected_algos[0]["key"],
                "match": "le al",
            }
        )
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_algos[:1]}
        )

    def test_algo_list_cross_assets_filters(self):
        """Filter algos on other asset key such as compute_plan_key, dataset_key and data_sample_key"""
        compute_plan = factory.create_computeplan()
        data_manager = factory.create_datamanager()
        data_sample = factory.create_datasample([data_manager])

        factory.create_computetask(
            compute_plan, self.algos[0], data_manager=data_manager, data_samples=[data_sample.key]
        )
        factory.create_computetask(compute_plan, self.algos[1])

        # filter on compute_plan_key
        params = urlencode({"compute_plan_key": compute_plan.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_algos[:2])

        # filter on dataset_key
        params = urlencode({"dataset_key": data_manager.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_algos[:1])

        # filter on data_sample_key
        params = urlencode({"data_sample_key": data_sample.key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_algos[:1])

    def test_algo_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_algos),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_algos[::-1]),

    @parameterized.expand(
        [
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_algo_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        self.assertEqual(r["count"], len(self.expected_algos))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_algos[offset : offset + page_size])

    def test_algo_cp_list_success(self):
        """List algos for a specific compute plan (CPAlgoViewSet)."""

        compute_plan = factory.create_computeplan()
        factory.create_computetask(compute_plan, self.algos[0])
        factory.create_computetask(compute_plan, self.algos[1])

        url = reverse("api:compute_plan_algo-list", args=[compute_plan.key])
        response = self.client.get(url, **self.extra)
        self.assertEqual(
            response.json(),
            {
                "count": len(self.expected_algos[:2]),
                "next": None,
                "previous": None,
                "results": self.expected_algos[:2],
            },
        )

    def test_algo_list_can_process(self):
        public_algo = Algo.objects.get(key=self.expected_algos[0]["key"])
        public_algo.permissions_process_public = True
        public_algo.save()
        self.expected_algos[0]["permissions"]["process"]["public"] = True

        shared_algo = Algo.objects.get(key=self.expected_algos[1]["key"])
        shared_algo.permissions_process_authorized_ids = ["MyOrg1MSP", "MyOrg2MSP"]
        shared_algo.save()
        self.expected_algos[1]["permissions"]["process"]["authorized_ids"] = ["MyOrg1MSP", "MyOrg2MSP"]

        params = urlencode({"can_process": "MyOrg1MSP"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_algos),

        params = urlencode({"can_process": "MyOrg2MSP"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_algos[:2]),

        params = urlencode({"can_process": "MyOrg3MSP"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), [self.expected_algos[0]]),

        params = urlencode({"can_process": "MyOrg1MSP,MyOrg2MSP"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_algos[:2]),

    @parameterized.expand(
        [
            (category, filename)
            for category in [
                AlgoCategory.simple,
                AlgoCategory.aggregate,
                AlgoCategory.composite,
                AlgoCategory.metric,
                AlgoCategory.predict,
            ]
            for filename in [
                "algo.tar.gz",
                "algo.zip",
            ]
        ]
    )
    def test_algo_create(self, category, filename):
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
                "algorithm": data["algorithm"],
                "inputs": data["inputs"],
                "outputs": data["outputs"],
            }

        algorithm_path = os.path.join(FIXTURE_PATH, filename)
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
            "file": open(algorithm_path, "rb"),
            "description": open(description_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_algo", side_effect=mock_orc_response):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        self.assertIsNotNone(response.data["key"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # asset created in local db
        self.assertEqual(Algo.objects.count(), len(self.expected_algos) + 1)

        data["file"].close()
        data["description"].close()

    @override_settings(DATA_UPLOAD_MAX_SIZE=150)
    def test_file_size_limit(self):
        algorithm_path = os.path.join(FIXTURE_PATH, "algo.tar.gz")
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
            "file": open(algorithm_path, "rb"),
            "description": open(description_path, "rb"),
        }

        response = self.client.post(self.url, data=data, format="multipart", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File too large", response.data["message"][0]["file"])

        data["description"].close()
        data["file"].close()

    def test_algo_create_fail_rollback(self):
        class MockOrcError(OrcError):
            def __init__(self) -> None:
                pass

            code = StatusCode.ALREADY_EXISTS
            details = "already exists"

        algorithm_path = os.path.join(FIXTURE_PATH, "algo.tar.gz")
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
            "file": open(algorithm_path, "rb"),
            "description": open(description_path, "rb"),
        }

        with mock.patch.object(OrchestratorClient, "register_algo", side_effect=MockOrcError()):
            response = self.client.post(self.url, data=data, format="multipart", **self.extra)
        # asset not created in local db
        self.assertEqual(Algo.objects.count(), len(self.expected_algos))
        # orc error code should be propagated
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    @internal_server_error_on_exception()
    @mock.patch("api.views.algo.AlgoViewSet.create", side_effect=Exception("Unexpected error"))
    def test_algo_create_fail(self, _):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_algo_retrieve(self):
        url = reverse("api:algo-detail", args=[self.expected_algos[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.expected_algos[0])

    def test_algo_retrieve_wrong_channel(self):
        url = reverse("api:algo-detail", args=[self.expected_algos[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_algo_retrieve_storage_addresses_update(self):
        algo = Algo.objects.get(key=self.expected_algos[0]["key"])
        algo.description_address.replace("http://testserver", "http://remotetestserver")
        algo.algorithm_address.replace("http://testserver", "http://remotetestserver")
        algo.save()

        url = reverse("api:algo-detail", args=[self.expected_algos[0]["key"]])
        response = self.client.get(url, **self.extra)
        for field in ("description", "algorithm"):
            self.assertEqual(response.data[field]["storage_address"], self.expected_algos[0][field]["storage_address"])

    @internal_server_error_on_exception()
    @mock.patch("api.views.algo.AlgoViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_algo_retrieve_fail(self, _):
        url = reverse("api:algo-detail", args=[self.expected_algos[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_algo_download_file(self):
        algo_files = factory.create_algo_files()
        algo = factory.create_algo(key=algo_files.key)
        url = reverse("api:algo-file", args=[algo.key])
        with mock.patch("api.views.utils.get_owner", return_value=algo.owner):
            response = self.client.get(url, **self.extra)
        content = response.getvalue()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content, algo_files.file.read())
        self.assertEqual(compute_hash(content), algo_files.checksum)

    def test_algo_download_description(self):
        algo_files = factory.create_algo_files()
        algo = factory.create_algo(key=algo_files.key)
        url = reverse("api:algo-description", args=[algo.key])
        with mock.patch("api.views.utils.get_owner", return_value=algo.owner):
            response = self.client.get(url, **self.extra)
        content = response.getvalue()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content, algo_files.description.read())

    def test_algo_update(self):
        algo = self.expected_algos[0]
        data = {
            "key": algo["key"],
            "name": "Bar",
        }

        url = reverse("api:algo-detail", args=[algo["key"]])
        algo["name"] = data["name"]

        with mock.patch.object(OrchestratorClient, "update_algo", side_effect=algo):
            response = self.client.put(url, data=data, format="json", **self.extra)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        error = OrcError()
        error.code = StatusCode.INTERNAL

        with mock.patch.object(OrchestratorClient, "update_algo", side_effect=error):
            response = self.client.put(url, data=data, format="json", **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

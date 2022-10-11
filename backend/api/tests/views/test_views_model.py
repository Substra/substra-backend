import logging
import os
import shutil
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from api.errors import AssetPermissionError
from api.models import Model
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient
from api.tests.common import internal_server_error_on_exception
from api.views.model import ModelPermissionViewSet
from organization.authentication import OrganizationUser
from substrapp.tests.common import get_sample_model
from substrapp.utils import compute_hash

CHANNEL = "mychannel"
TEST_ORG = "MyTestOrg"
MODEL_KEY = "some-key"
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    LEDGER_MSP_ID=TEST_ORG,
)
class ModelViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.model, self.model_filename = get_sample_model()
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": CHANNEL, "HTTP_ACCEPT": "application/json;version=0.0"}
        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)
        self.url = reverse("api:model-list")

        compute_plan = factory.create_computeplan()

        simple_algo = factory.create_algo(
            outputs=factory.build_algo_outputs(["model"]),
        )
        self.train_task = factory.create_computetask(
            compute_plan,
            simple_algo,
            outputs=factory.build_computetask_outputs(simple_algo),
        )
        simple_model_1 = factory.create_model(self.train_task, identifier="model")
        simple_model_2 = factory.create_model(self.train_task, identifier="model")

        composite_algo = factory.create_algo(
            outputs=factory.build_algo_outputs(["local", "shared"]),
        )
        composite_task = factory.create_computetask(
            compute_plan,
            composite_algo,
            outputs=factory.build_computetask_outputs(composite_algo),
        )
        local_model = factory.create_model(composite_task, identifier="local")

        self.expected_results = [
            {
                "key": str(simple_model_1.key),
                "compute_task_key": str(self.train_task.key),
                "address": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/model/{simple_model_1.key}/file/",
                },
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
                "owner": "MyOrg1MSP",
                "creation_date": simple_model_1.creation_date.isoformat().replace("+00:00", "Z"),
            },
            {
                "key": str(simple_model_2.key),
                "compute_task_key": str(self.train_task.key),
                "address": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/model/{simple_model_2.key}/file/",
                },
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
                "owner": "MyOrg1MSP",
                "creation_date": simple_model_2.creation_date.isoformat().replace("+00:00", "Z"),
            },
            {
                "key": str(local_model.key),
                "compute_task_key": str(composite_task.key),
                "address": {
                    "checksum": "dummy-checksum",
                    "storage_address": f"http://testserver/model/{local_model.key}/file/",
                },
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
                "owner": "MyOrg1MSP",
                "creation_date": local_model.creation_date.isoformat().replace("+00:00", "Z"),
            },
        ]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        self.logger.setLevel(self.previous_level)

    def test_model_list_empty(self):
        Model.objects.all().delete()
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_model_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_model_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    @internal_server_error_on_exception()
    @mock.patch("api.views.model.ModelViewSet.list", side_effect=Exception("Unexpected error"))
    def test_model_list_fail(self, _):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_model_list_storage_addresses_update(self):
        for model in Model.objects.all():
            model.model_address.replace("http://testserver", "http://remotetestserver")
            model.save()

        response = self.client.get(self.url, **self.extra)
        self.assertEqual(response.data["count"], len(self.expected_results))
        for result, model in zip(response.data["results"], self.expected_results):
            self.assertEqual(result["address"]["storage_address"], model["address"]["storage_address"])

    def test_model_list_filter(self):
        """Filter model on key."""
        key = self.expected_results[0]["key"]
        params = urlencode({"key": key})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_model_list_filter_and(self):
        """Filter model on key and owner."""
        key, owner = self.expected_results[0]["key"], self.expected_results[0]["owner"]
        params = urlencode({"key": key, "owner": owner})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 1, "next": None, "previous": None, "results": self.expected_results[:1]}
        )

    def test_model_list_filter_in(self):
        """Filter model in key_0, key_1."""
        key_0 = self.expected_results[0]["key"]
        key_1 = self.expected_results[1]["key"]
        params = urlencode({"key": ",".join([key_0, key_1])})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(
            response.json(), {"count": 2, "next": None, "previous": None, "results": self.expected_results[:2]}
        )

    @parameterized.expand(
        [
            ("page_size_1_page_3", 1, 3),
            ("page_size_2_page_2", 2, 2),
            ("page_size_3_page_1", 3, 1),
        ]
    )
    def test_model_list_pagination_success(self, _, page_size, page):
        params = urlencode({"page_size": page_size, "page": page})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        r = response.json()
        self.assertEqual(r["count"], len(self.expected_results))
        offset = (page - 1) * page_size
        self.assertEqual(r["results"], self.expected_results[offset : offset + page_size])

    def test_model_list_ordering(self):
        params = urlencode({"ordering": "creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results),

        params = urlencode({"ordering": "-creation_date"})
        response = self.client.get(f"{self.url}?{params}", **self.extra)
        self.assertEqual(response.json().get("results"), self.expected_results[::-1])

    def test_model_retrieve(self):
        url = reverse("api:model-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.json(), self.expected_results[0])

    def test_model_retrieve_wrong_channel(self):
        url = reverse("api:model-detail", args=[self.expected_results[0]["key"]])
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_model_retrieve_storage_addresses_update(self):
        model = Model.objects.get(key=self.expected_results[0]["key"])
        model.model_address.replace("http://testserver", "http://remotetestserver")
        model.save()

        url = reverse("api:model-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(
            response.data["address"]["storage_address"], self.expected_results[0]["address"]["storage_address"]
        )

    @internal_server_error_on_exception()
    @mock.patch("api.views.model.ModelViewSet.retrieve", side_effect=Exception("Unexpected error"))
    def test_model_retrieve_fail(self, _):
        url = reverse("api:model-detail", args=[self.expected_results[0]["key"]])
        response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_model_download_by_organization_for_worker(self):
        """ "Simple organization-to-organization download, e.g. worker downloads in-model"""
        pvs = ModelPermissionViewSet()

        pvs.check_access(
            CHANNEL,
            OrganizationUser(),
            factory.create_model(self.train_task, public=True),
            is_proxied_request=False,
        )

        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                OrganizationUser(),
                factory.create_model(self.train_task, public=False),
                is_proxied_request=False,
            )

        pvs.check_access(
            CHANNEL,
            OrganizationUser(username="foo"),
            factory.create_model(self.train_task, public=False, owner="foo"),
            is_proxied_request=False,
        )

    @override_settings(LEDGER_CHANNELS={CHANNEL: {"model_export_enabled": True}})
    def test_model_export_proxied(self):
        """Model export (proxied) with option enabled"""
        pvs = ModelPermissionViewSet()

        pvs.check_access(
            CHANNEL,
            OrganizationUser(),
            factory.create_model(self.train_task, public=True),
            is_proxied_request=True,
        )

        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                OrganizationUser(),
                factory.create_model(self.train_task, public=False),
                is_proxied_request=True,
            )

        pvs.check_access(
            CHANNEL,
            OrganizationUser(username="foo"),
            factory.create_model(self.train_task, public=False, owner="foo"),
            is_proxied_request=True,
        )

    @override_settings(LEDGER_CHANNELS={CHANNEL: {"model_export_enabled": False}})
    def test_model_download_by_organization_proxied_option_disabled(self):
        """Model export (proxied) with option disabled"""
        pvs = ModelPermissionViewSet()

        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                OrganizationUser(),
                factory.create_model(self.train_task, public=True),
                is_proxied_request=True,
            )

    @override_settings(LEDGER_CHANNELS={CHANNEL: {"model_export_enabled": True}})
    def test_model_download_by_classic_user_enabled(self):
        """Model export (by end-user, not proxied) with option enabled"""
        pvs = ModelPermissionViewSet()

        pvs.check_access(
            CHANNEL,
            User(),
            factory.create_model(self.train_task, public=True),
            is_proxied_request=False,
        )

        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                User(),
                factory.create_model(self.train_task, public=False),
                is_proxied_request=False,
            )

    @override_settings(LEDGER_CHANNELS={CHANNEL: {"model_export_enabled": False}})
    def test_model_download_by_classic_user_disabled(self):
        """Model export (by end-user, not proxied) with option disabled"""
        pvs = ModelPermissionViewSet()

        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                User(),
                factory.create_model(self.train_task, public=True),
                is_proxied_request=False,
            )

    @override_settings(LEDGER_CHANNELS={CHANNEL: {}})
    def test_model_download_by_classic_user_default(self):
        pvs = ModelPermissionViewSet()

        # Access to model download should be denied because the "model_export_enabled"
        # option is not specified in the app configuration.
        with self.assertRaises(AssetPermissionError):
            pvs.check_access(
                CHANNEL,
                User(),
                factory.create_model(self.train_task, public=True),
                is_proxied_request=False,
            )

    def test_model_download_file(self):
        model_files = factory.create_model_files()
        model = factory.create_model(self.train_task, key=model_files.key, owner="substra")
        url = reverse("api:model-file", args=[model.key])
        with mock.patch("api.views.utils.get_owner", return_value=model.owner), mock.patch(
            "api.views.model.type", return_value=OrganizationUser
        ):
            response = self.client.get(url, **self.extra)
        content = response.getvalue()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content, model_files.file.read())
        self.assertEqual(compute_hash(content), model_files.checksum)

    def test_model_download_file_wrong_user(self):
        model_files = factory.create_model_files()
        model = factory.create_model(self.train_task, key=model_files.key, owner="substra")
        url = reverse("api:model-file", args=[model.key])
        with mock.patch("api.views.utils.get_owner", return_value=model.owner):
            response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_model_download_file_wrong_owner(self):
        model_files = factory.create_model_files()
        model = factory.create_model(self.train_task, key=model_files.key, owner="owkin")
        url = reverse("api:model-file", args=[model.key])
        with mock.patch("api.views.utils.get_owner", return_value=model.owner), mock.patch(
            "api.views.model.type", return_value=OrganizationUser
        ):
            response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_model_download_file_deleted(self):
        model_files = factory.create_model_files()
        model = factory.create_model(self.train_task, key=model_files.key, owner="substra")
        # delete intermediary model
        model.model_address = None
        model.save()
        url = reverse("api:model-file", args=[model.key])
        with mock.patch("api.views.utils.get_owner", return_value=model.owner), mock.patch(
            "api.views.model.type", return_value=OrganizationUser
        ):
            response = self.client.get(url, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_410_GONE)

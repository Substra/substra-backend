import os
import shutil
import tempfile
from unittest import mock

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from node.authentication import NodeUser
from substrapp.models import Model
from substrapp.tests import factory
from substrapp.utils import compute_hash

from ..common import AuthenticatedClient
from ..common import get_sample_model

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class ModelQueryTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.model, _ = get_sample_model()
        self.extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }
        algo = factory.create_algo()
        compute_plan = factory.create_computeplan()
        self.compute_task = factory.create_computetask(compute_plan, algo)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_get_head_model_ok(self):
        checksum = compute_hash(self.model.read(), key="key_traintuple")
        head_model = Model.objects.create(file=self.model, checksum=checksum)
        metadata = factory.create_model(self.compute_task, key=head_model.key, public=False, owner="substra")
        with mock.patch("substrapp.views.utils.get_owner", return_value=metadata.owner), mock.patch(
            "substrapp.views.model.type", return_value=NodeUser
        ):
            response = self.client.get(f"/model/{head_model.key}/file/", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(head_model.checksum, compute_hash(response.getvalue(), key="key_traintuple"))

    def test_get_head_model_ko_user(self):
        checksum = compute_hash(self.model.read(), key="key_traintuple")
        head_model = Model.objects.create(file=self.model, checksum=checksum)
        metadata = factory.create_model(self.compute_task, key=head_model.key, public=False, owner="substra")

        with mock.patch("substrapp.views.utils.get_owner", return_value=metadata.owner):
            response = self.client.get(f"/model/{head_model.key}/file/", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_head_model_ko_wrong_node(self):
        checksum = compute_hash(self.model.read(), key="key_traintuple")
        head_model = Model.objects.create(file=self.model, checksum=checksum)
        metadata = factory.create_model(self.compute_task, key=head_model.key, public=False, owner="owkin")
        with mock.patch("substrapp.views.utils.get_owner", return_value=metadata.owner), mock.patch(
            "substrapp.views.model.type", return_value=NodeUser
        ):
            response = self.client.get(f"/model/{head_model.key}/file/", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_deleted_intermediary_model(self):
        metadata = factory.create_model(self.compute_task, public=True)
        metadata.model_address = None
        metadata.save()
        with mock.patch("substrapp.views.utils.get_owner", return_value=metadata.owner), mock.patch(
            "substrapp.views.model.type", return_value=NodeUser
        ):
            response = self.client.get(f"/model/{metadata.key}/file/", **self.extra)
            self.assertEqual(response.status_code, status.HTTP_410_GONE)

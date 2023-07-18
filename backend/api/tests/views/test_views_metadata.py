import os
import shutil
import tempfile

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from api.models import ComputePlan
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
)
class ComputePlanMetadataViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.compute_plan = factory.create_computeplan(metadata=dict(one="one", two=2, three="3"))
        self.compute_plan = factory.create_computeplan(
            metadata=dict(One="case_sensitive", three="duplicate_three", four="test")
        )

        self.url = reverse("api:compute_plan_metadata-list")

        # alphabetically ordered list
        self.expected_results = ["four", "one", "One", "three", "two"]

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_metadata_list_empty(self):
        ComputePlan.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(list(response.data), [])

    def test_metadata_list(self):
        response = self.client.get(self.url)
        self.assertEqual(list(response.data), self.expected_results)

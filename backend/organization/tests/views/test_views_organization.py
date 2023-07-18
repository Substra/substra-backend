import logging
import os
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from api.serializers import ChannelOrganizationSerializer as OrganizationRepSerializer
from api.tests.common import AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
)
class ModelViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.logger = logging.getLogger("django.request")
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

        for organization_id in ["foo", "bar"]:
            serializer = OrganizationRepSerializer(
                data={"id": organization_id, "channel": "mychannel", "creation_date": "2022-01-20T14:18:53.785788Z"}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def tearDown(self):
        self.logger.setLevel(self.previous_level)

    def test_organization_list_success(self):
        url = reverse("organization:organization-list")
        with mock.patch("api.serializers.organization.get_owner", return_value="foo"):
            response = self.client.get(url)
            self.assertEqual(
                response.json(),
                [
                    {"id": "bar", "address": "", "is_current": False, "creation_date": "2022-01-20T14:18:53.785788Z"},
                    {"id": "foo", "address": "", "is_current": True, "creation_date": "2022-01-20T14:18:53.785788Z"},
                ],
            )

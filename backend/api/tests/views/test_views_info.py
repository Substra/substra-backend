from unittest import mock

from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from api.tests.common import AuthenticatedClient
from orchestrator.client import OrchestratorClient
from orchestrator.resources import OrchestratorVersion


@override_settings(CHANNELS={"mychannel": {"model_export_enabled": True}})
class InfoViewTests(APITestCase):
    url = "/info/"

    def test_anonymous(self):
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        assert "host" in data
        assert "organization_id" in data
        assert "organization_name" in data
        self.assertEqual(data["config"], {})
        assert "version" not in data
        assert "orchestrator_version" not in data

    def test_authenticated(self):
        client = AuthenticatedClient()

        with mock.patch.object(OrchestratorClient, "query_version", return_value=OrchestratorVersion(server="foo")):
            response = client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        assert "host" in data
        assert "organization_id" in data
        assert "organization_name" in data
        assert "config" in data
        assert "model_export_enabled" in data["config"]
        assert "version" in data
        assert data["orchestrator_version"] == "foo"

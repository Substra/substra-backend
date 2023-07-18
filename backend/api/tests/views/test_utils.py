import os
import shutil
import tempfile
import uuid
from unittest import mock

import pytest
import responses
from django.test import override_settings
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from api.errors import BadRequestError
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedClient
from api.views.utils import validate_metadata
from organization.authentication import OrganizationUser
from organization.models import OutgoingOrganization
from substrapp.models import Function as FunctionFiles
from substrapp.tests.common import get_description_function
from substrapp.tests.common import get_sample_function

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}})
class PermissionMixinDownloadFileTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.function_file, self.function_filename = get_sample_function()
        self.function_file.seek(0)
        self.function_content = self.function_file.read()
        self.function_description_file, self.function_description_filename = get_description_function()
        self.function_key = uuid.uuid4()
        self.function_url = reverse("api:function-file", kwargs={"pk": self.function_key})
        self.extra = {
            "HTTP_SUBSTRA_CHANNEL_NAME": "mychannel",
            "HTTP_ACCEPT": "application/json;version=0.0",
        }

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_download_file_local_allowed(self):
        """Asset is local (owner is local-organization) and local-organization in authorized ids."""
        FunctionFiles.objects.create(
            key=self.function_key, file=self.function_file, description=self.function_description_file
        )
        metadata = factory.create_function(key=self.function_key, public=False, owner="local-organization")
        self.assertIn("local-organization", metadata.permissions_process_authorized_ids)

        with mock.patch("api.views.utils.get_owner", return_value="local-organization"):
            response = self.client.get(self.function_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers["Content-Disposition"], f'attachment; filename="{self.function_filename}"')
        self.assertEqual(response.getvalue(), self.function_content)

    def test_download_file_local_denied(self):
        """Asset is local (owner is local-organization) and local-organization NOT in authorized ids."""
        FunctionFiles.objects.create(
            key=self.function_key, file=self.function_file, description=self.function_description_file
        )
        metadata = factory.create_function(key=self.function_key, public=False, owner="local-organization")
        metadata.permissions_process_authorized_ids = []
        metadata.save()

        with mock.patch("api.views.utils.get_owner", return_value="local-organization"):
            response = self.client.get(self.function_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_download_file_remote_allowed(self):
        """Asset is remote (owner is remote-organization) and local-organization in authorized ids."""
        metadata = factory.create_function(key=self.function_key, public=True, owner="remote-organization")
        metadata.permissions_process_authorized_ids = ["remote-organization", "local-organization"]
        metadata.save()
        OutgoingOrganization.objects.create(organization_id="remote-organization", secret="s3cr37")

        with mock.patch(
            "api.views.utils.get_owner", return_value="local-organization"
        ), responses.RequestsMock() as mocked_responses:
            mocked_responses.add(
                responses.GET,
                metadata.function_address,
                body=self.function_content,
                content_type="text/plain; charset=utf-8",
            )
            response = self.client.get(self.function_url)
            mocked_responses.assert_call_count(metadata.function_address, 1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.getvalue(), self.function_content)

    def test_download_file_remote_denied(self):
        """Asset is remote (owner is remote-organization) and local-organization NOT in authorized ids."""
        metadata = factory.create_function(key=self.function_key, public=False, owner="remote-organization")
        metadata.permissions_process_authorized_ids = ["remote-organization"]
        metadata.save()

        self.client.force_authenticate(user=OrganizationUser(username="local-organization"))
        response = self.client.get(self.function_url, **self.extra)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@parameterized.expand(
    [
        ({}, False),
        ({"foo": "bar"}, False),
        ({"_foo_": "bar"}, False),
        ({"foo": "bar__"}, False),
        ({"foo__bar": "foo"}, True),
        ({"__foo": "bar"}, True),
        ({"foo__": "bar"}, True),
    ]
)
def test_validate_metadata(metadata, raises):
    if raises:
        with pytest.raises(BadRequestError):
            validate_metadata(metadata)
    else:
        validate_metadata(metadata)

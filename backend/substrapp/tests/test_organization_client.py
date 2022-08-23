import contextlib
from unittest import mock

import pytest
import requests
from rest_framework import status

from organization.models import OutgoingOrganization
from substrapp.clients import organization as organization_client
from substrapp.exceptions import IntegrityError
from substrapp.utils import compute_hash

CHANNEL = "mychannel"


@pytest.fixture
def organization_id(db):
    organization_id = "external_organization_id"
    OutgoingOrganization.objects.create(organization_id=organization_id, secret="s3cr37")
    return organization_id


def mock_response(status_code: int, content: bytes):
    """Returns a mock instance of an HTTP Response."""
    is_ok = status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
    response = mock.Mock(requests.Response)
    response.status_code = status_code
    response.content = content
    response.ok = is_ok
    response.iter_content.return_value = [response.content]

    if not is_ok:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    return response


@contextlib.contextmanager
def patch_requests_get(status_code=status.HTTP_200_OK, content=None):
    """Returns a mock instance of requests.get."""
    with mock.patch("substrapp.clients.organization._http_request") as requests_get:
        requests_get.return_value = mock_response(status_code, content)
        yield requests_get


def test_get():
    url = "http://fake_address"
    expected_content = b"some remote content"
    checksum = compute_hash(expected_content)
    organization_id = "myorg"

    with patch_requests_get(content=expected_content) as requests_get:
        content = organization_client.get(CHANNEL, organization_id, url, checksum)
        requests_get.assert_called_once()
    assert content == expected_content


def test_get_failure_invalid_checksum():
    url = "http://fake_address"
    expected_content = b"some remote content"
    invalid_checksum = "boo"
    organization_id = "myorg"

    with patch_requests_get(content=expected_content) as requests_get:
        with pytest.raises(IntegrityError):
            organization_client.get(CHANNEL, organization_id, url, invalid_checksum)
            requests_get.assert_called_once()


def test_download(tmpdir):
    url = "http://fake_address"
    expected_content = b"some remote content"
    checksum = compute_hash(expected_content)
    destination = tmpdir / "asset.file"
    organization_id = "myorg"

    with patch_requests_get(content=expected_content) as requests_get:
        organization_client.download(CHANNEL, organization_id, url, destination, checksum)
        requests_get.assert_called_once()

    assert destination.exists()
    content = destination.read_binary()
    assert content == expected_content


def test_download_failure_invalid_checksum(tmpdir):
    url = "http://fake_address"
    expected_content = b"some remote content"
    invalid_checksum = "boo"
    destination = tmpdir / "asset.file"
    organization_id = "myorg"

    with patch_requests_get(content=expected_content) as requests_get:
        with pytest.raises(IntegrityError):
            organization_client.download(CHANNEL, organization_id, url, destination, invalid_checksum)
        requests_get.assert_called_once()

    assert not destination.exists()


@pytest.mark.parametrize(
    "input_header, expected_header",
    [
        (
            {},
            {
                "Accept": "application/json;version=0.0",
                "Substra-Channel-Name": "mychannel",
            },
        ),
        (
            {"Custom-header": "True"},
            {
                "Accept": "application/json;version=0.0",
                "Substra-Channel-Name": "mychannel",
                "Custom-header": "True",
            },
        ),
    ],
)
def test_headers(input_header, expected_header):
    channel = "mychannel"
    assert organization_client._add_mandatory_headers(input_header, channel) == expected_header


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ((None, False), {}),
        ((None, True), {"stream": True}),
        (({"test": "mydata"}, False), {"data": {"test": "mydata"}}),
        (({}, False), {"data": {}}),
    ],
)
def test_kwargs(test_input, expected):
    assert organization_client._http_request_kwargs(*test_input) == expected


def test_fetch_secret(organization_id):
    assert organization_client._fetch_secret(organization_id) == "s3cr37"

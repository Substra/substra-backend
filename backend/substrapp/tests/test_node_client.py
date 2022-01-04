import contextlib
from unittest import mock

import pytest
import requests
from rest_framework import status

from node.models import OutgoingNode
from substrapp.clients import node as node_client
from substrapp.exceptions import IntegrityError
from substrapp.utils import compute_hash

CHANNEL = "mychannel"


@pytest.fixture
def node_id(db):
    node_id = "external_node_id"
    OutgoingNode.objects.create(node_id=node_id, secret="s3cr37")
    return node_id


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
    with mock.patch("substrapp.clients.node.requests.get") as requests_get:
        requests_get.return_value = mock_response(status_code, content)
        yield requests_get


def test_get(node_id):
    url = "http://fake_address"
    expected_content = b"some remote content"
    checksum = compute_hash(expected_content)

    with patch_requests_get(content=expected_content) as requests_get:
        content = node_client.get(CHANNEL, node_id, url, checksum)
        requests_get.assert_called_once()
    assert content == expected_content


def test_get_failure_invalid_checksum(node_id):
    url = "http://fake_address"
    expected_content = b"some remote content"
    invalid_checksum = "boo"

    with patch_requests_get(content=expected_content) as requests_get:
        with pytest.raises(IntegrityError):
            node_client.get(CHANNEL, node_id, url, invalid_checksum)
            requests_get.assert_called_once()


def test_download(node_id, tmpdir):
    url = "http://fake_address"
    expected_content = b"some remote content"
    checksum = compute_hash(expected_content)
    destination = tmpdir / "asset.file"

    with patch_requests_get(content=expected_content) as requests_get:
        node_client.download(CHANNEL, node_id, url, destination, checksum)
        requests_get.assert_called_once()

    assert destination.exists()
    content = destination.read_binary()
    assert content == expected_content


def test_download_failure_invalid_checksum(node_id, tmpdir):
    url = "http://fake_address"
    expected_content = b"some remote content"
    invalid_checksum = "boo"
    destination = tmpdir / "asset.file"

    with patch_requests_get(content=expected_content) as requests_get:
        with pytest.raises(IntegrityError):
            node_client.download(CHANNEL, node_id, url, destination, invalid_checksum)
        requests_get.assert_called_once()

    assert not destination.exists()

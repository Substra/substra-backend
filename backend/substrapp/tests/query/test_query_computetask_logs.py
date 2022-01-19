import io
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from unittest import mock

import pytest
import responses
from django import conf
from django import urls
from django.core import files
from rest_framework import response as drf_response
from rest_framework import status
from rest_framework import test

from node import authentication as node_auth
from node import models as node_models
from orchestrator import client as orc_client
from substrapp import models
from substrapp import utils
from substrapp.views import utils as view_utils


@pytest.fixture
def compute_task_failure_report() -> models.ComputeTaskFailureReport:
    file = files.File(io.BytesIO(b"Hello, World!"))
    compute_task_key = "1abe0aae-0308-49a0-8c57-238bfecdbcc0"
    failure_report = models.ComputeTaskFailureReport(
        compute_task_key=compute_task_key, logs_checksum=utils.get_hash(file)
    )
    failure_report.logs.save(name=compute_task_key, content=file, save=True)
    return failure_report


def get_compute_task(key: str, owner: str, authorized_ids: List[str]) -> Dict[str, Any]:
    return {
        "key": key,
        "owner": owner,
        "logs_permission": {"public": False, "authorized_ids": authorized_ids},
    }


def get_failure_report(compute_task_key: str, logs_address: str) -> Dict[str, Union[str, Dict[str, str]]]:
    return {
        "compute_task_key": compute_task_key,
        "logs_address": {
            "checksum": "dummy checksum",
            "storage_address": logs_address,
        },
    }


def get_logs(key: str, client: test.APIClient, **extra) -> drf_response.Response:
    url = urls.reverse("substrapp:logs-file", kwargs={"pk": key})
    return client.get(url, **extra)


def test_download_logs_failure_unauthenticated(api_client: test.APIClient):
    """An unauthenticated user cannot download logs."""
    res = get_logs(key="13c2c61e-ffe5-476f-a7fd-dd6a132f4480", client=api_client)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@mock.patch.object(orc_client.OrchestratorClient, "get_failure_report")
@mock.patch.object(orc_client.OrchestratorClient, "query_task")
def test_download_local_logs_success(
    mocked_query_task: mock.Mock,
    mocked_get_failure_report: mock.Mock,
    compute_task_failure_report,
    authenticated_client: test.APIClient,
):
    """An authorized user download logs located on the node."""

    compute_task_key = str(compute_task_failure_report.compute_task_key)
    owner = conf.settings.LEDGER_MSP_ID

    mocked_query_task.return_value = get_compute_task(key=compute_task_key, owner=owner, authorized_ids=[owner])
    mocked_get_failure_report.return_value = get_failure_report(
        compute_task_key, compute_task_failure_report.logs_address
    )

    res = get_logs(key=compute_task_key, client=authenticated_client)

    assert res.status_code == status.HTTP_200_OK
    assert res.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert res.headers["Content-Disposition"] == f'attachment; filename="tuple_logs_{compute_task_key}.txt"'
    assert res.getvalue() == compute_task_failure_report.logs.read()
    mocked_query_task.assert_called_once()
    mocked_get_failure_report.assert_called_once()


@pytest.mark.django_db
@mock.patch.object(orc_client.OrchestratorClient, "query_task")
def test_download_logs_failure_forbidden(
    mocked_query_task: mock.Mock,
    compute_task_failure_report,
    authenticated_client: test.APIClient,
):
    """An authenticated user cannot download logs if he is not authorized."""

    compute_task_key = str(compute_task_failure_report.compute_task_key)

    owner = "foo"
    assert owner != conf.settings.LEDGER_MSP_ID

    mocked_query_task.return_value = get_compute_task(key=compute_task_key, owner=owner, authorized_ids=[owner])

    res = get_logs(key=compute_task_key, client=authenticated_client)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    mocked_query_task.assert_called_once()


@pytest.mark.django_db
@mock.patch.object(orc_client.OrchestratorClient, "get_failure_report")
@mock.patch.object(orc_client.OrchestratorClient, "query_task")
def test_download_local_logs_failure_not_found(
    mocked_query_task: mock.Mock,
    mocked_get_failure_report: mock.Mock,
    compute_task_failure_report,
    authenticated_client: test.APIClient,
):
    """An authorized user attempt to download logs that are not referenced in the database."""

    compute_task_key = str(compute_task_failure_report.compute_task_key)
    owner = conf.settings.LEDGER_MSP_ID

    mocked_query_task.return_value = get_compute_task(key=compute_task_key, owner=owner, authorized_ids=[owner])
    mocked_get_failure_report.return_value = get_failure_report(
        compute_task_key, compute_task_failure_report.logs_address
    )

    compute_task_failure_report.delete()

    res = get_logs(key=compute_task_key, client=authenticated_client)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    mocked_query_task.assert_called_once()
    mocked_get_failure_report.assert_called_once()


@pytest.mark.django_db
@mock.patch.object(orc_client.OrchestratorClient, "get_failure_report")
@mock.patch.object(orc_client.OrchestratorClient, "query_task")
def test_download_remote_logs_success(
    mocked_query_task: mock.Mock, mocked_get_failure_report: mock.Mock, authenticated_client: test.APIClient
):
    """An authorized user download logs on a remote node by using his node as proxy."""

    compute_task_key = "13c2c61e-ffe5-476f-a7fd-dd6a132f4480"
    current_node = conf.settings.LEDGER_MSP_ID
    outgoing_node = "outgoing-node"
    storage_address = f"https://another-node.foo.com/logs/{compute_task_key}"
    logs_content = b"Lorem ipsum dolor sit amet"

    node_models.OutgoingNode.objects.create(node_id=outgoing_node, secret=node_models.Node.generate_secret())

    mocked_query_task.return_value = get_compute_task(
        key=compute_task_key, owner=outgoing_node, authorized_ids=[outgoing_node, current_node]
    )
    mocked_get_failure_report.return_value = get_failure_report(compute_task_key, storage_address)

    with responses.RequestsMock() as mocked_responses:
        mocked_responses.add(
            responses.GET, storage_address, body=logs_content, content_type="text/plain; charset=utf-8"
        )

        res = get_logs(key=compute_task_key, client=authenticated_client)

        mocked_responses.assert_call_count(storage_address, 1)

    assert res.status_code == status.HTTP_200_OK
    assert res.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert res.headers["Content-Disposition"] == f'attachment; filename="tuple_logs_{compute_task_key}.txt"'
    assert res.getvalue() == logs_content
    mocked_query_task.assert_called_once()
    mocked_get_failure_report.assert_called_once()


@pytest.fixture
def incoming_node_user(settings: conf.Settings) -> node_auth.NodeUser:
    incoming_node = "incoming-node"
    settings.LEDGER_CHANNELS.update({incoming_node: {"chaincode": {"name": "mycc2"}}})
    return node_auth.NodeUser(username=incoming_node)


def get_proxy_headers(channel_name: str) -> Dict[str, str]:
    return {view_utils.HTTP_HEADER_PROXY_ASSET: "True", "HTTP_SUBSTRA_CHANNEL_NAME": channel_name}


@pytest.mark.django_db
@mock.patch.object(orc_client.OrchestratorClient, "get_failure_report")
@mock.patch.object(orc_client.OrchestratorClient, "query_task")
def test_node_download_logs_success(
    mocked_query_task: mock.Mock,
    mocked_get_failure_report: mock.Mock,
    compute_task_failure_report,
    api_client: test.APIClient,
    incoming_node_user: node_auth.NodeUser,
):
    """An authorized node can download logs from another node."""

    compute_task_key = str(compute_task_failure_report.compute_task_key)
    owner = conf.settings.LEDGER_MSP_ID
    incoming_node = incoming_node_user.username
    authorized_ids = [owner, incoming_node]

    mocked_query_task.return_value = get_compute_task(key=compute_task_key, owner=owner, authorized_ids=authorized_ids)
    mocked_get_failure_report.return_value = get_failure_report(
        compute_task_key, compute_task_failure_report.logs_address
    )

    api_client.force_authenticate(user=incoming_node_user)
    extra_headers = get_proxy_headers(incoming_node_user.username)
    res = get_logs(key=compute_task_key, client=api_client, **extra_headers)

    assert res.status_code == status.HTTP_200_OK
    assert res.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert res.headers["Content-Disposition"] == f'attachment; filename="tuple_logs_{compute_task_key}.txt"'
    assert res.getvalue() == compute_task_failure_report.logs.read()
    mocked_query_task.assert_called_once()
    mocked_get_failure_report.assert_called_once()


@pytest.mark.django_db
@mock.patch.object(orc_client.OrchestratorClient, "query_task")
def test_node_download_logs_forbidden(
    mocked_query_task: mock.Mock,
    compute_task_failure_report,
    api_client: test.APIClient,
    incoming_node_user: node_auth.NodeUser,
):
    """An unauthorized node cannot download logs from another node."""

    compute_task_key = str(compute_task_failure_report.compute_task_key)
    owner = conf.settings.LEDGER_MSP_ID
    incoming_node = incoming_node_user.username
    authorized_ids = [owner]

    assert owner != incoming_node

    mocked_query_task.return_value = get_compute_task(key=compute_task_key, owner=owner, authorized_ids=authorized_ids)

    api_client.force_authenticate(user=incoming_node_user)
    extra_headers = get_proxy_headers(incoming_node)
    res = get_logs(key=compute_task_key, client=api_client, **extra_headers)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    mocked_query_task.assert_called_once()

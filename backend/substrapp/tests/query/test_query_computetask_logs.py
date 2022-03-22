import io
import uuid

import pytest
import responses
from django import conf
from django import urls
from django.core import files
from rest_framework import response as drf_response
from rest_framework import status
from rest_framework import test

from localrep.models import ComputeTask
from node import authentication as node_auth
from node import models as node_models
from substrapp import utils
from substrapp.models import ComputeTaskFailureReport
from substrapp.tests import factory
from substrapp.views import utils as view_utils


@pytest.fixture
def compute_task_failure_report() -> tuple[ComputeTask, ComputeTaskFailureReport]:
    file = files.File(io.BytesIO(b"Hello, World!"))
    compute_task_key = uuid.uuid4()
    failure_report = ComputeTaskFailureReport(
        compute_task_key=compute_task_key,
        logs_checksum=utils.get_hash(file),
    )
    failure_report.logs.save(name=compute_task_key, content=file, save=True)

    # create computetask metadata in localrep
    compute_task = factory.create_computetask(
        factory.create_computeplan(),
        factory.create_algo(),
        key=compute_task_key,
        public=False,
        owner=conf.settings.LEDGER_MSP_ID,
    )
    return compute_task, failure_report


def get_logs(key: uuid.uuid4, client: test.APIClient, **extra) -> drf_response.Response:
    url = urls.reverse("substrapp:logs-file", kwargs={"pk": str(key)})
    return client.get(url, **extra)


def test_download_logs_failure_unauthenticated(api_client: test.APIClient):
    """An unauthenticated user cannot download logs."""
    res = get_logs(key=uuid.uuid4(), client=api_client)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_download_local_logs_success(
    compute_task_failure_report,
    authenticated_client: test.APIClient,
):
    """An authorized user download logs located on the node."""

    compute_task, failure_report = compute_task_failure_report
    assert compute_task.owner == conf.settings.LEDGER_MSP_ID  # local
    assert conf.settings.LEDGER_MSP_ID in compute_task.logs_permission_authorized_ids  # allowed

    res = get_logs(key=compute_task.key, client=authenticated_client)

    assert res.status_code == status.HTTP_200_OK
    assert res.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert res.headers["Content-Disposition"] == f'attachment; filename="tuple_logs_{compute_task.key}.txt"'
    assert res.getvalue() == failure_report.logs.read()


@pytest.mark.django_db
def test_download_logs_failure_forbidden(
    compute_task_failure_report,
    authenticated_client: test.APIClient,
):
    """An authenticated user cannot download logs if he is not authorized."""

    compute_task, failure_report = compute_task_failure_report
    assert compute_task.owner == conf.settings.LEDGER_MSP_ID  # local
    compute_task.logs_permission_authorized_ids = []  # not allowed
    compute_task.save()

    res = get_logs(key=str(compute_task.key), client=authenticated_client)

    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_download_local_logs_failure_not_found(
    compute_task_failure_report,
    authenticated_client: test.APIClient,
):
    """An authorized user attempt to download logs that are not referenced in the database."""

    compute_task, failure_report = compute_task_failure_report
    assert compute_task.owner == conf.settings.LEDGER_MSP_ID  # local
    assert conf.settings.LEDGER_MSP_ID in compute_task.logs_permission_authorized_ids  # allowed
    failure_report.delete()  # not found

    res = get_logs(key=compute_task.key, client=authenticated_client)

    assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_download_remote_logs_success(
    compute_task_failure_report,
    authenticated_client: test.APIClient,
):
    """An authorized user download logs on a remote node by using his node as proxy."""

    compute_task, failure_report = compute_task_failure_report
    outgoing_node = "outgoing-node"
    compute_task.logs_owner = outgoing_node  # remote
    compute_task.logs_permission_authorized_ids = [conf.settings.LEDGER_MSP_ID, outgoing_node]  # allowed
    compute_task.save()
    node_models.OutgoingNode.objects.create(node_id=outgoing_node, secret=node_models.Node.generate_secret())

    logs_content = failure_report.logs.read()
    with responses.RequestsMock() as mocked_responses:
        mocked_responses.add(
            responses.GET,
            compute_task.logs_address,
            body=logs_content,
            content_type="text/plain; charset=utf-8",
        )
        res = get_logs(key=compute_task.key, client=authenticated_client)

        mocked_responses.assert_call_count(compute_task.logs_address, 1)

    assert res.status_code == status.HTTP_200_OK
    assert res.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert res.headers["Content-Disposition"] == f'attachment; filename="tuple_logs_{compute_task.key}.txt"'
    assert res.getvalue() == logs_content


@pytest.fixture
def incoming_node_user(settings: conf.Settings) -> node_auth.NodeUser:
    incoming_node = "incoming-node"
    settings.LEDGER_CHANNELS.update({incoming_node: {"chaincode": {"name": "mycc2"}}})
    return node_auth.NodeUser(username=incoming_node)


def get_proxy_headers(channel_name: str) -> dict[str, str]:
    return {view_utils.HTTP_HEADER_PROXY_ASSET: "True", "HTTP_SUBSTRA_CHANNEL_NAME": channel_name}


@pytest.mark.django_db
def test_node_download_logs_success(
    compute_task_failure_report,
    api_client: test.APIClient,
    incoming_node_user: node_auth.NodeUser,
):
    """An authorized node can download logs from another node."""

    compute_task, failure_report = compute_task_failure_report
    compute_task.logs_owner = conf.settings.LEDGER_MSP_ID  # local (incoming request from remote)
    compute_task.logs_permission_authorized_ids = [
        conf.settings.LEDGER_MSP_ID,
        incoming_node_user.username,
    ]  # incoming user allowed
    compute_task.channel = incoming_node_user.username
    compute_task.save()

    api_client.force_authenticate(user=incoming_node_user)
    extra_headers = get_proxy_headers(incoming_node_user.username)
    res = get_logs(key=compute_task.key, client=api_client, **extra_headers)

    assert res.status_code == status.HTTP_200_OK
    assert res.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert res.headers["Content-Disposition"] == f'attachment; filename="tuple_logs_{compute_task.key}.txt"'
    assert res.getvalue() == failure_report.logs.read()


@pytest.mark.django_db
def test_node_download_logs_forbidden(
    compute_task_failure_report,
    api_client: test.APIClient,
    incoming_node_user: node_auth.NodeUser,
):
    """An unauthorized node cannot download logs from another node."""

    compute_task, failure_report = compute_task_failure_report
    compute_task.logs_owner = conf.settings.LEDGER_MSP_ID  # local (incoming request from remote)
    compute_task.logs_permission_authorized_ids = [conf.settings.LEDGER_MSP_ID]  # incoming user not allowed
    compute_task.channel = incoming_node_user.username
    compute_task.save()

    api_client.force_authenticate(user=incoming_node_user)
    extra_headers = get_proxy_headers(incoming_node_user.username)
    res = get_logs(key=compute_task.key, client=api_client, **extra_headers)

    assert res.status_code == status.HTTP_403_FORBIDDEN

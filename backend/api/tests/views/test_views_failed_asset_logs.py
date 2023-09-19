import uuid

import pytest
import responses
from django import conf
from django import urls
from rest_framework import response as drf_response
from rest_framework import status
from rest_framework import test

from api.models import ComputeTask
from api.tests import asset_factory as factory
from api.views import utils as view_utils
from organization import authentication as organization_auth
from organization import models as organization_models
from substrapp.models import AssetFailureReport


@pytest.fixture
def asset_failure_report() -> tuple[ComputeTask, AssetFailureReport]:
    compute_task = factory.create_computetask(
        factory.create_computeplan(),
        factory.create_function(),
        public=False,
        owner=conf.settings.LEDGER_MSP_ID,
    )
    failure_report = factory.create_computetask_logs(compute_task.key)
    return compute_task, failure_report


def get_logs(key: uuid.uuid4, client: test.APIClient, **extra) -> drf_response.Response:
    url = urls.reverse("api:logs-file", kwargs={"pk": str(key)})
    return client.get(url, **extra)


def test_download_logs_failure_unauthenticated(api_client: test.APIClient):
    """An unauthenticated user cannot download logs."""
    res = get_logs(key=uuid.uuid4(), client=api_client)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_download_local_logs_success(
    asset_failure_report,
    authenticated_client: test.APIClient,
):
    """An authorized user download logs located on the organization."""

    compute_task, failure_report = asset_failure_report
    assert compute_task.owner == conf.settings.LEDGER_MSP_ID  # local
    assert conf.settings.LEDGER_MSP_ID in compute_task.logs_permission_authorized_ids  # allowed

    res = get_logs(key=compute_task.key, client=authenticated_client)

    assert res.status_code == status.HTTP_200_OK
    assert res.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert res.headers["Content-Disposition"] == f'attachment; filename="tuple_logs_{compute_task.key}.txt"'
    assert res.getvalue() == failure_report.logs.read()


@pytest.mark.django_db
def test_download_logs_failure_forbidden(
    asset_failure_report,
    authenticated_client: test.APIClient,
):
    """An authenticated user cannot download logs if he is not authorized."""

    compute_task, failure_report = asset_failure_report
    assert compute_task.owner == conf.settings.LEDGER_MSP_ID  # local
    compute_task.logs_permission_authorized_ids = []  # not allowed
    compute_task.save()

    res = get_logs(key=str(compute_task.key), client=authenticated_client)

    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_download_local_logs_failure_not_found(
    asset_failure_report,
    authenticated_client: test.APIClient,
):
    """An authorized user attempt to download logs that are not referenced in the database."""

    compute_task, failure_report = asset_failure_report
    assert compute_task.owner == conf.settings.LEDGER_MSP_ID  # local
    assert conf.settings.LEDGER_MSP_ID in compute_task.logs_permission_authorized_ids  # allowed
    failure_report.delete()  # not found

    res = get_logs(key=compute_task.key, client=authenticated_client)

    assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_download_remote_logs_success(
    asset_failure_report,
    authenticated_client: test.APIClient,
):
    """An authorized user download logs on a remote organization by using his organization as proxy."""

    compute_task, failure_report = asset_failure_report
    outgoing_organization = "outgoing-organization"
    compute_task.logs_owner = outgoing_organization  # remote
    compute_task.logs_permission_authorized_ids = [conf.settings.LEDGER_MSP_ID, outgoing_organization]  # allowed
    compute_task.save()
    organization_models.OutgoingOrganization.objects.create(
        organization_id=outgoing_organization, secret=organization_models.Organization.generate_password()
    )

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
def incoming_organization_user(settings: conf.Settings) -> organization_auth.OrganizationUser:
    incoming_organization = "incoming-organization"
    settings.LEDGER_CHANNELS.update({incoming_organization: {"chaincode": {"name": "mycc2"}}})
    return organization_auth.OrganizationUser(username=incoming_organization)


def get_proxy_headers(channel_name: str) -> dict[str, str]:
    return {view_utils.HTTP_HEADER_PROXY_ASSET: "True", "HTTP_SUBSTRA_CHANNEL_NAME": channel_name}


@pytest.mark.django_db
def test_organization_download_logs_success(
    asset_failure_report,
    api_client: test.APIClient,
    incoming_organization_user: organization_auth.OrganizationUser,
):
    """An authorized organization can download logs from another organization."""

    compute_task, failure_report = asset_failure_report
    compute_task.logs_owner = conf.settings.LEDGER_MSP_ID  # local (incoming request from remote)
    compute_task.logs_permission_authorized_ids = [
        conf.settings.LEDGER_MSP_ID,
        incoming_organization_user.username,
    ]  # incoming user allowed
    compute_task.channel = incoming_organization_user.username
    compute_task.save()

    api_client.force_authenticate(user=incoming_organization_user)
    extra_headers = get_proxy_headers(incoming_organization_user.username)
    res = get_logs(key=compute_task.key, client=api_client, **extra_headers)

    assert res.status_code == status.HTTP_200_OK
    assert res.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert res.headers["Content-Disposition"] == f'attachment; filename="tuple_logs_{compute_task.key}.txt"'
    assert res.getvalue() == failure_report.logs.read()


@pytest.mark.django_db
def test_organization_download_logs_forbidden(
    asset_failure_report,
    api_client: test.APIClient,
    incoming_organization_user: organization_auth.OrganizationUser,
):
    """An unauthorized organization cannot download logs from another organization."""

    compute_task, failure_report = asset_failure_report
    compute_task.logs_owner = conf.settings.LEDGER_MSP_ID  # local (incoming request from remote)
    compute_task.logs_permission_authorized_ids = [conf.settings.LEDGER_MSP_ID]  # incoming user not allowed
    compute_task.channel = incoming_organization_user.username
    compute_task.save()

    api_client.force_authenticate(user=incoming_organization_user)
    extra_headers = get_proxy_headers(incoming_organization_user.username)
    res = get_logs(key=compute_task.key, client=api_client, **extra_headers)

    assert res.status_code == status.HTTP_403_FORBIDDEN

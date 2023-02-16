import pytest
from django.contrib.auth.hashers import check_password

from organization.models import IncomingOrganization

ORGANIZATION_ID = "organization_id"
PASSWORD = "p@sswr0d44"


def test_incoming_organization_manager_password_and_secret():
    incoming_organization_manager = IncomingOrganization.objects

    with pytest.raises(ValueError):
        incoming_organization_manager.create(organization_id=ORGANIZATION_ID, secret=PASSWORD, password=PASSWORD)


def test_incoming_organization_manager_secret_not_valid():
    incoming_organization_manager = IncomingOrganization.objects

    with pytest.raises(ValueError):
        incoming_organization_manager.create(organization_id=ORGANIZATION_ID, secret=PASSWORD)


@pytest.mark.django_db
def test_incoming_organization_manager_password():
    incoming_organization_manager = IncomingOrganization.objects
    incoming_organization_manager.create(organization_id=ORGANIZATION_ID, password=PASSWORD)
    incoming_organization = incoming_organization_manager.get(organization_id=ORGANIZATION_ID)

    assert check_password(PASSWORD, incoming_organization.secret)

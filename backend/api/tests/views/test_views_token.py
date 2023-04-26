import os
import tempfile
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status

from users.models.token import BearerToken

MEDIA_ROOT = tempfile.mkdtemp()
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURE_PATH = os.path.abspath(os.path.join(DIR_PATH, "../../../../fixtures/chunantes/datasamples"))

ORG_SETTINGS = {
    "MEDIA_ROOT": MEDIA_ROOT,
    "LEDGER_CHANNELS": {"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
}


@pytest.mark.django_db
def test_delete_token(authenticated_client):
    authenticated_client.create_user()
    user = authenticated_client.user
    token = BearerToken.objects.create(user=user)

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1

    url = f"/active-api-tokens/?id={token.token_id}"
    # url = reverse("backend:active-bearer-tokens-delete")
    # url = reverse("backend:active_bearer_tokens-delete")
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_200_OK

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 0


@pytest.mark.django_db
def test_multiple_token(authenticated_client, api_client):
    authenticated_client.create_user()
    user = authenticated_client.user
    token_1 = BearerToken.objects.create(user=user)
    token_2 = BearerToken.objects.create(user=user)

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 2

    valid_auth_token_header = f"Token {token_2}"
    api_client.credentials(HTTP_AUTHORIZATION=valid_auth_token_header)

    response = api_client.get("/active-api-tokens/")
    assert response.status_code == status.HTTP_200_OK

    url = f"/active-api-tokens/?id={token_2.token_id}"
    # url = reverse("backend:active-bearer-tokens-delete")
    # url = reverse("backend:active_bearer_tokens-delete")
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_200_OK

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1
    # token_2 was already deleted so trying to use it should result in 401
    valid_auth_token_header = f"Token {token_2}"
    api_client.credentials(HTTP_AUTHORIZATION=valid_auth_token_header)
    response = api_client.get("/active-api-tokens/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # token_1 is still valid
    valid_auth_token_header = f"Token {token_1}"
    api_client.credentials(HTTP_AUTHORIZATION=valid_auth_token_header)
    response = api_client.get("/active-api-tokens/")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_expiring_token(authenticated_client, api_client):
    authenticated_client.create_user()
    user = authenticated_client.user
    # create a token that expired a day ago
    token = BearerToken.objects.create(user=user, expiry=timezone.now() - timedelta(days=1))

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1

    valid_auth_token_header = f"Token {token}"
    api_client.credentials(HTTP_AUTHORIZATION=valid_auth_token_header)

    response = api_client.get("/active-api-tokens/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    url = f"/active-api-tokens/?id={token.token_id}"
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1


@pytest.mark.django_db
def test_delete_token_other_user(authenticated_client):
    other_user = User.objects.create(username="user-2")
    other_user.set_password("p@sswr0d44")
    other_user.save()
    token = BearerToken.objects.create(user=other_user)

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1

    url = f"/active-api-tokens/?id={token.token_id}"
    # url = reverse("backend:active-bearer-tokens-delete")
    # url = reverse("backend:active_bearer_tokens-delete")
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1

from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.utils import timezone
from rest_framework import status

from users.models.token import BearerToken


@pytest.mark.django_db
def test_cannot_create_non_expiring_token(authenticated_client):
    authenticated_client.create_user()
    user = authenticated_client.user
    # create a token without expiration date
    with pytest.raises(IntegrityError):
        BearerToken.objects.create(user=user)


@pytest.mark.django_db
def test_delete_token(authenticated_client):
    authenticated_client.create_user()
    user = authenticated_client.user
    token = BearerToken.objects.create(user=user, expires_at=timezone.now() + timedelta(days=1))

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1

    url = f"/active-api-tokens/?id={token.id}"
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_200_OK

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 0


@pytest.mark.django_db
def test_multiple_token(authenticated_client, api_client):
    authenticated_client.create_user()
    user = authenticated_client.user
    token_1 = BearerToken.objects.create(user=user, expires_at=timezone.now() + timedelta(days=1))
    token_2 = BearerToken.objects.create(user=user, expires_at=timezone.now() + timedelta(days=2))

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 2

    valid_auth_token_header = f"Token {token_2}"
    api_client.credentials(HTTP_AUTHORIZATION=valid_auth_token_header)

    response = api_client.get("/active-api-tokens/")
    assert response.status_code == status.HTTP_200_OK

    url = f"/active-api-tokens/?id={token_2.id}"
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
def test_expired_token(authenticated_client, api_client):
    authenticated_client.create_user()
    user = authenticated_client.user
    # create a token that expired a day ago
    token = BearerToken.objects.create(user=user, expires_at=timezone.now() - timedelta(days=1))

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1

    valid_auth_token_header = f"Token {token}"
    api_client.credentials(HTTP_AUTHORIZATION=valid_auth_token_header)

    response = api_client.get("/active-api-tokens/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    url = f"/active-api-tokens/?id={token.id}"
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1


@pytest.mark.django_db
def test_delete_token_other_user(authenticated_client):
    other_user = User.objects.create(username="user-2")
    other_user.set_password("p@sswr0d44")
    other_user.save()
    token = BearerToken.objects.create(user=other_user, expires_at=timezone.now() + timedelta(days=1))

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1

    url = f"/active-api-tokens/?id={token.id}"
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1


@pytest.mark.django_db
def test_token_creation_post(authenticated_client):
    authenticated_client.create_user()
    payload = {"expires_at": "2023-07-14T11:55:36.509Z", "note": "gfyqgbs"}
    url = "/api-token/"
    response = authenticated_client.post(url, payload)
    assert response.status_code == status.HTTP_200_OK

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 1


@pytest.mark.django_db
def test_cannot_post_token_wo_expires_at(authenticated_client):
    authenticated_client.create_user()
    payload = {}
    url = "/api-token/"
    response = authenticated_client.post(url, payload)

    assert response.json() == {"expires_at": ["This field is required."]}
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    tokens_count = BearerToken.objects.count()
    assert tokens_count == 0

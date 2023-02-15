from urllib.parse import urlencode

import pytest
from django.urls.base import reverse
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APIClient

from api.tests.common import AuthenticatedClient
from users.models.user_channel import UserChannel


class TestUserEndpoints:
    url = None
    extra = None

    @pytest.fixture(autouse=True)
    def use_dummy_channels(self, settings):
        settings.LEDGER_CHANNELS = {"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}

    @classmethod
    def setup_class(cls):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.url = reverse("user:users-list")
        cls.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "mychannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        cls.channel = "mychannel"

    @pytest.mark.django_db
    def test_user_create_success(self):
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43"}

        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data.get("username") == data["username"]
        assert response.data.get("role") == UserChannel.Role.USER

    @pytest.mark.django_db
    def test_user_create_unauthorized(self):
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43"}

        response = APIClient().post(self.url, data=data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_user_create_duplicate(self):
        data = {"username": "substra", "password": "pas$w0rdtestofdrea6S43"}

        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("username")[0] == "A user with that username already exists."

    @pytest.mark.django_db
    def test_user_create_short_password(self):
        data = {"username": "toto", "password": "password"}

        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_user_create_empty_password(self):
        data = {"username": "toto", "password": ""}

        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_user_create_role_admin(self):
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43", "role": "ADMIN"}

        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_user_create_creator_not_admin(self):
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43"}

        response = AuthenticatedClient(channel=self.channel).post(self.url, data=data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_user_create_role_unknown(self):
        data = {
            "username": "toto",
            "password": "pas$w0rdtestofdrea6S43",
            "role": "NONEXISTING",
        }

        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_retrieve_user(self):
        url = reverse("user:users-detail", args=["substra"])
        response = AuthenticatedClient(channel=self.channel).get(url, **self.extra)
        assert response.status_code == status.HTTP_200_OK

    @parameterized.expand(
        [
            ({"role": UserChannel.Role.USER},),
            ({"password": "newpas$w0rdtestofdrea6S43"},),
            ({"ui_preferences": {"columns": ["col1", "col2"]}},),
            ({"role": UserChannel.Role.USER, "ui_preferences": {"columns": ["col1"]}},),
        ]
    )
    @pytest.mark.django_db
    def test_update_user(self, data):
        url = reverse("user:users-detail", args=["substra"])
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).put(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        for key in data:
            if key != "password":
                assert response.data[key] == data[key]

    @pytest.mark.django_db
    def test_update_password_unauthorized(self):
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43"}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED

        url = reverse("user:users-password", args=["toto"])
        data = {"password": "newpas$w0rdtestofdrea6S43"}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).put(url, data=data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_update_password_empty(self):
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43"}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED

        url = reverse("user:users-password", args=["toto"])
        data = {"password": ""}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).put(url, data=data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_request_reset_token(self):
        url = reverse("user:users-reset-password", args=["substra"])
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(url, data={})

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("reset_password_token") is not None

    @pytest.mark.django_db
    def test_request_reset_token_unauthorized(self):
        url = reverse("user:users-reset-password", args=["substra"])
        response = AuthenticatedClient(role=UserChannel.Role.USER, channel=self.channel).post(url, data={})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_verify_token(self):
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43"}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED

        url = reverse("user:users-reset-password", args=["toto"])
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(url, data={})
        assert response.status_code == status.HTTP_200_OK

        url = reverse("user:users-verify-token", args=["toto"])
        params = urlencode({"token": response.data.get("reset_password_token")})
        response = APIClient().get(f"{url}?{params}")

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_verify_token_failure(self):
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43"}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED

        url = reverse("user:users-verify-token", args=["toto"])
        params = urlencode({"token": "not a valid token"})
        response = APIClient().get(f"{url}?{params}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_set_new_passord(self):
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43"}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED

        url = reverse("user:users-reset-password", args=["toto"])
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(url, data={})
        token = response.data.get("reset_password_token")
        assert response.status_code == status.HTTP_200_OK

        url = reverse("user:users-set-password", args=["toto"])
        data = {"token": response.data.get("reset_password_token"), "password": "pas$w0rdtestofdrea6S44"}
        response = APIClient().post(url, data=data)
        assert response.status_code == status.HTTP_200_OK

        url = reverse("user:users-verify-token", args=["toto"])
        params = urlencode({"token": token})
        response = APIClient().get(f"{url}?{params}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_set_new_passord_failure(self):
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43"}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED

        url = reverse("user:users-set-password", args=["toto"])
        data = {"token": "not-valid-token", "password": "pas$w0rdtestofdrea6S44"}
        response = APIClient().post(url, data=data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_delete_user(self):
        url = reverse("user:users-detail", args=["substra"])
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_list_users(self):
        response = AuthenticatedClient(channel=self.channel).get(self.url, **self.extra)

        assert response.status_code == status.HTTP_200_OK
        assert "substra" == response.json()["results"][0]["username"]
        assert "mychannel" == response.json()["results"][0]["channel"]
        assert "USER" == response.json()["results"][0]["role"]
        assert 1 == response.json()["count"]

    @pytest.mark.django_db
    def test_filter_user_role(self):
        # create admin user
        data = {"username": "toto", "password": "pas$w0rdtestofdrea6S43", "role": "USER"}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED

        # list all users (no filter)
        response = AuthenticatedClient(channel=self.channel).get(self.url, **self.extra)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 2
        assert {user["role"] for user in data["results"]} == {"USER", "ADMIN"}

        # list only admin users
        response = AuthenticatedClient(channel=self.channel).get(self.url, data={"role": "ADMIN"}, **self.extra)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["role"] == "ADMIN"

        # list only non admin users
        response = AuthenticatedClient(channel=self.channel).get(self.url, data={"role": "USER"}, **self.extra)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["role"] == "USER"

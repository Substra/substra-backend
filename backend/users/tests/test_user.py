from urllib.parse import urlencode

import pytest
from django.contrib.auth import get_user_model
from django.urls.base import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.tests.common import AuthenticatedClient
from users import utils
from users.models.user_channel import UserChannel


class TestUserUtil:
    def test_username_sanitizing(self):
        data = {
            "scott.TIGER": "scott-tiger",
            " --Hello guys,! How are you? 🙂": "hello-guys-how-are-you",
            "---hello-guys---how--are-you--": "hello-guys-how-are-you",
            # accents stripped out but stuff that are their own letters are kept as-is (unicode NFKD policy)
            "Bôñjöūr! ¿Çå va̋ møn čœűr?": "bonjour-ca-va-m-n-c-ur",
            # sanitize can return empty strings
            """廣東，喺南嶺南邊，面臨南中國海。بَندَرعَبّاس مرکز استان هرمزگان و شهرستان بندرعباس در جنوب ایران است.""": "",
        }
        for k, v in data.items():
            assert utils.utils.sanitize(k) == v

    def test_email_address_splitting(self):
        valid_addresses = {
            """email@example.com""": ("email", "example.com"),
            """firstname.lastname@example.com""": ("firstname.lastname", "example.com"),
            """email@subdomain.example.com""": ("email", "subdomain.example.com"),
            """firstname+lastname@example.com""": ("firstname+lastname", "example.com"),
            """email@123.123.123.123""": ("email", "123.123.123.123"),
            """email@[123.123.123.123]""": ("email", "123.123.123.123"),
            """"email"@example.com""": ("email", "example.com"),
            """" "@example.com""": (" ", "example.com"),
            """mailhost!username@example.com""": ("mailhost!username", "example.com"),
            """1234567890@example.com""": ("1234567890", "example.com"),
            """email@example-one.com""": ("email", "example-one.com"),
            """email@example.name""": ("email", "example.name"),
            """email@example.museum""": ("email", "example.museum"),
            """email@example.co.jp""": ("email", "example.co.jp"),
            """firstname-lastname@example.com""": ("firstname-lastname", "example.com"),
            """test/test@test.com""": ("test/test", "test.com"),
            """" "@example.com""": (" ", "example.com"),
            """mailhost!username@example.com""": ("mailhost!username", "example.com"),
            """_______@example.com""": ("_______", "example.com"),
            """postmaster@[IPv6:2001:0db8:85a3:0000:0000:8a2e:0370:7334]""": (
                "postmaster",
                "IPv6:2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            ),
            r"""much.”more\ unusual”@example.com""": (r"""much.”more\ unusual”""", "example.com"),
            r""""very.(),:;<>[]\".VERY.\"very@\\ \"very\".unusual"@strange.example.com""": (
                r"""very.(),:;<>[]\".VERY.\"very@\\ \"very\".unusual""",
                "strange.example.com",
            ),
        }
        for address, decomposition in valid_addresses.items():
            assert utils.utils.split_email_addr(address) == decomposition

    @pytest.mark.django_db
    def test_username_iteration(self):
        user_model = get_user_model()
        user_model.objects.create_user("toto", email="toto@example.com")
        assert utils.utils.iterate_username("toto") == "toto-2"

        user_model.objects.create_user("toto-2", email="toto@example.com")
        user_model.objects.create_user("toto-3", email="toto@example.com")
        user_model.objects.create_user("toto-4", email="toto@example.com")
        assert utils.utils.iterate_username("toto") == "toto-5"

        for i in range(5, 10):
            user_model.objects.create_user(f"toto-{i}", email="toto@example.com")
        assert utils.utils.iterate_username("toto") == "toto-10"

    @pytest.mark.django_db
    def test_oidc_username_generation(self):
        user_model = get_user_model()
        args = {
            "email": "toto@example.com",
            "issuer": "example.com",
            "subject": "12345",
        }
        assert utils.oidc.generate_username(**args) == "toto"
        assert utils.oidc.generate_username_with_domain(**args) == "toto-example"

        user_model.objects.create_user("toto", email="toto@example.com")

        assert utils.oidc.generate_username(**args) != "toto"
        assert utils.oidc.generate_username_with_domain(**args) == "toto-example"

        weird_email_args = {
            "email": "👾🥱@😈.com",
            "issuer": "example.com",
            "subject": "12345",
        }
        assert utils.oidc.generate_username(**weird_email_args) != ""
        assert not user_model.objects.filter(username=utils.oidc.generate_username(**weird_email_args)).exists()
        assert utils.oidc.generate_username_with_domain(**weird_email_args) != ""
        assert not user_model.objects.filter(
            username=utils.oidc.generate_username_with_domain(**weird_email_args)
        ).exists()


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
        assert response.data.get("message") == "Username already exists"

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
        response = AuthenticatedClient(channel=self.channel).get(
            url,
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_update_role(self):
        url = reverse("user:users-detail", args=["substra"])
        data = {"role": UserChannel.Role.USER}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).put(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == UserChannel.Role.USER

    @pytest.mark.django_db
    def test_update_password(self):
        url = reverse("user:users-password", args=["substra"])
        data = {"password": "newpas$w0rdtestofdrea6S43"}
        response = AuthenticatedClient(role=UserChannel.Role.ADMIN, channel=self.channel).put(url, data=data)

        assert response.status_code == status.HTTP_200_OK

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
        response = AuthenticatedClient(channel=self.channel).get(
            self.url,
        )

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
        response = AuthenticatedClient(channel=self.channel).get(
            self.url,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 2
        assert {user["role"] for user in data["results"]} == {"USER", "ADMIN"}

        # list only admin users
        response = AuthenticatedClient(channel=self.channel).get(
            self.url,
            data={"role": "ADMIN"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["role"] == "ADMIN"

        # list only non admin users
        response = AuthenticatedClient(channel=self.channel).get(
            self.url,
            data={"role": "USER"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["role"] == "USER"

import base64
from http.cookies import SimpleCookie
from unittest import mock

from django.contrib.auth.models import User
from requests import auth
from rest_framework.test import APIClient

from organization.models import IncomingOrganization
from users.models.user_channel import UserChannel

# This function helper generate a basic authentication header with given credentials
# Given username and password it returns "Basic GENERATED_TOKEN"
from users.serializers import CustomTokenObtainPairSerializer


def generate_basic_auth_header(username, password):
    return "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()


def generate_jwt_auth_header(jwt):
    return "JWT " + jwt


class AuthenticatedClient(APIClient):
    def __init__(
        self,
        enforce_csrf_checks=False,
        role=UserChannel.Role.USER,
        channel=None,
        username="substra",
        password="p@sswr0d44",
        **defaults,
    ):
        super().__init__(enforce_csrf_checks, **defaults)
        self.role = role
        self.channel = channel
        self.username = username
        self.password = password

    def request(self, **kwargs):
        # create user
        user, created = User.objects.get_or_create(username=self.username)
        if created:
            user.set_password(self.password)
            user.save()
            # for testing purpose most authentication are done without channel allowing to mock passing channel in
            # header, this check is necessary to not break previous tests but irl a user cannot be created
            # without a channel
            if self.channel:
                UserChannel.objects.create(user=user, channel_name=self.channel, role=self.role)

        # simulate login
        serializer = CustomTokenObtainPairSerializer(data={"username": self.username, "password": self.password})

        serializer.is_valid()
        data = serializer.validated_data
        access_token = str(data.access_token)

        # simulate right httpOnly cookie and Authorization jwt
        jwt_auth_header = generate_jwt_auth_header(".".join(access_token.split(".")[0:2]))
        self.credentials(HTTP_AUTHORIZATION=jwt_auth_header)
        self.cookies = SimpleCookie({"signature": access_token.split(".")[2]})

        return super().request(**kwargs)


class AuthenticatedBackendClient(APIClient):
    def request(self, **kwargs):
        username = "MyTestOrg"
        password = "p@sswr0d44"
        try:
            IncomingOrganization.objects.get(organization_id=username)
        except IncomingOrganization.DoesNotExist:
            IncomingOrganization.objects.create(organization_id=username, password=password)

        self.credentials(HTTP_AUTHORIZATION=auth._basic_auth_str(username, password))

        return super().request(**kwargs)


def internal_server_error_on_exception():
    """Decorator factory to make the Django test client respond with '500 Internal Server Error'
    when an unhandled exception occurs.

    Once we update to Django 3, we can use the `raise_request_exception` parameter
    of the test client: https://docs.djangoproject.com/en/3.2/topics/testing/tools/#making-requests.

    Adapted from https://stackoverflow.com/a/62720158.
    """
    return mock.patch("django.test.client.Client.store_exc_info", mock.Mock())

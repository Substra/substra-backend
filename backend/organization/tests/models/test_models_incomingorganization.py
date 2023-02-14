from typing import Type

from django.contrib.auth import hashers
from django.contrib.auth.hashers import BasePasswordHasher
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.test import TestCase

from organization.models import IncomingOrganization


# Cf Django 4.1 release notes https://docs.djangoproject.com/en/dev/releases/4.1
class PBKDF2PasswordDefault40Hasher(PBKDF2PasswordHasher):
    algorithm = "pbkdf2_4_0"
    iterations = 320_000


# Cf Django 4.2 release notes https://docs.djangoproject.com/en/dev/releases/4.2
class PBKDF2PasswordDefault41Hasher(PBKDF2PasswordHasher):
    algorithm = "pbkdf2_4_1"
    iterations = 600_000


class IncomingOrganizationTests(TestCase):
    def assert_previous_hasher_upgrade(self, previous_hasher_class: Type[BasePasswordHasher]):
        password = "p@sswr0d44"
        organization_id = "test_organization_id"
        previous_algorithm = previous_hasher_class.algorithm
        previous_iterations = previous_hasher_class.iterations
        previous_qualifed_path = f"{previous_hasher_class.__module__}.{previous_hasher_class.__name__}"

        # Set our hasher as first so it will be used as default in backend/organization/models.py#L45
        with self.modify_settings(
            PASSWORD_HASHERS={
                "prepend": previous_qualifed_path,
            }
        ):
            incoming_organization = IncomingOrganization.objects.create(
                organization_id=organization_id, password=password
            )
            secret = incoming_organization.secret
            assert secret.startswith(f"{previous_algorithm}${previous_iterations}")
            assert hashers.check_password(password, incoming_organization.secret)

        # Set our hasher as last so we can still valdiate our password
        # but incoming_organization.check_password will upgrade to default
        with self.modify_settings(
            PASSWORD_HASHERS={
                "append": previous_qualifed_path,
            }
        ):
            current_hasher = hashers.get_hasher()
            incoming_organization.check_password(password)
            new_secret = incoming_organization.secret
            assert current_hasher.algorithm != previous_algorithm
            assert current_hasher.iterations != previous_iterations
            assert new_secret.startswith(f"{current_hasher.algorithm}${current_hasher.iterations}")
            assert hashers.check_password(password, incoming_organization.secret)

    def test_password_upgrade_from_4_0_to_4_1(self):
        self.assert_previous_hasher_upgrade(PBKDF2PasswordDefault40Hasher)

    def test_password_upgrade_from_4_1_to_4_2(self):
        self.assert_previous_hasher_upgrade(PBKDF2PasswordDefault41Hasher)

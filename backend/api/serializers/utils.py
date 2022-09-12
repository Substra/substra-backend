import structlog
from django.conf import settings
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.errors import AlreadyExistsError
from api.models.utils import URLValidatorWithOptionalTLD

logger = structlog.get_logger(__name__)


class URLFieldWithOptionalTLD(serializers.CharField):
    """Use patched URLValidatorWithOptionalTLD."""

    default_error_messages = {"invalid": _("Enter a valid URL.")}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        validator = URLValidatorWithOptionalTLD(message=self.error_messages["invalid"])
        self.validators.append(validator)


def make_addressable_serializer(field_name):
    class AddressableSerializer(serializers.Serializer):
        storage_address = URLFieldWithOptionalTLD(source=f"{field_name}_address")
        checksum = serializers.CharField(max_length=64, source=f"{field_name}_checksum")

    return AddressableSerializer


def make_permission_serializer(field_name, public=True):
    class PrivatePermissionSerializer(serializers.Serializer):
        authorized_ids = serializers.ListField(
            source=f"{field_name}_authorized_ids",
            child=serializers.CharField(),
        )

    class PublicPermissionSerializer(PrivatePermissionSerializer):
        public = serializers.BooleanField(source=f"{field_name}_public")

    return PublicPermissionSerializer if public else PrivatePermissionSerializer


def make_download_process_permission_serializer(prefix="", public=True):
    class PermissionsSerializer(serializers.Serializer):
        download = make_permission_serializer(f"{prefix}permissions_download", public)(source="*")
        process = make_permission_serializer(f"{prefix}permissions_process", public)(source="*")

    return PermissionsSerializer


class SafeSerializerMixin:
    """Catch conflicts as data could be simultaneously created from views and sync.
    Raises:
        AlreadyExistsError: the asset was already create
    """

    primary_key_name: str = "key"

    def save_if_not_exists(self):
        try:
            self.is_valid(raise_exception=True)
        except ValidationError:
            if self.primary_key_name in self.errors and len(self.errors) == 1:
                raise AlreadyExistsError
            raise

        try:
            with transaction.atomic():
                return self.save()
        except IntegrityError as err:
            # WARNING: side effect if another field name contains the pk-field name
            if self.primary_key_name in err.args[0]:
                raise AlreadyExistsError
            logger.warning("Failed to save asset", error=err.args[0])
            raise


def get_channel_choices() -> list[str]:
    """
    Get serializer choices from channels settings.
    """
    return list(settings.LEDGER_CHANNELS.keys())

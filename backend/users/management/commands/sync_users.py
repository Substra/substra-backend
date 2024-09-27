from django.config import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import models

from organization.management.commands.base_sync import BaseSyncCommand
from organization.management.commands.base_sync import Element
from users.models import UserChannel
from users.views.user import _validate_role


class UserElement(Element):
    channel: str


class Command(BaseSyncCommand):
    help = "Sync users"
    model_name = "User"
    field_key = "username"

    def __init__(self, *args, **kwargs):
        self.model = get_user_model()
        super().__init__(*args, **kwargs)

    def parse_line(self, line: str) -> UserElement:
        (key, password, channel) = line.split(" ")

        return UserElement(key=key, password=password, channel=channel)

    # Validate password, use specific function for creation and add UserChannel
    def create(self, element: UserElement) -> models.Model:
        try:
            validate_password(element.password, self.model(username=element.key))
        except ValidationError as err:
            self.stderr.write("\n".join(err.messages))
            return

        user = self.model.objects.create_user(username=element.key, password=element.password)
        self.stdout.write(f"{self.model_name} created: {element.key}, password={element.password}")
        UserChannel.objects.create(user=user, channel_name=element.channel, role=_validate_role("ADMIN"))
        self.stdout.write(f"User channel created: {element.key}")
        return user

    # Update password and user channel
    def update_password(self, element: UserElement) -> models.Model:
        user = super().update_password(element)
        user_channel = UserChannel.objects.get(user=user)
        user_channel.channel_name = element.channel
        user_channel.save()
        self.stdout.write(f"User channel updated: {element.key}")
        return user

    def delete(self, discarded_keys: set[str]) -> None:
        # Prevent the deletion of virtual users
        discarded_keys.difference_update(settings.VIRTUAL_USERNAMES.values())
        super().delete(discarded_keys)

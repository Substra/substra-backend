import uuid

from django.conf import settings
from django.db import models

from api.models import Function as APIFunction
from substrapp.utils import get_hash


def upload_to(instance, filename) -> str:
    return f"functions/{instance.key}/{filename}"


def upload_to_function(instance, filename) -> str:
    return upload_to(instance.function, filename)


class Function(models.Model):
    """Storage Data table"""

    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(
        storage=settings.FUNCTION_STORAGE, max_length=500, upload_to=upload_to
    )  # path max length to 500 instead of default 100
    description = models.FileField(
        storage=settings.FUNCTION_STORAGE, upload_to=upload_to, max_length=500
    )  # path max length to 500 instead of default 100
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs) -> None:
        """Use hash of file as checksum"""
        if not self.checksum and self.file:
            self.checksum = get_hash(self.file)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Function with key {self.key}"


class FunctionImage(models.Model):
    """Serialized Docker image"""

    function = models.OneToOneField(APIFunction, on_delete=models.CASCADE, primary_key=True)
    file = models.FileField(
        storage=settings.FUNCTION_STORAGE, max_length=500, upload_to=upload_to_function
    )  # path max length to 500 instead of default 100
    checksum = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs) -> None:
        """Use hash of file as checksum"""
        if not self.checksum and self.file:
            self.checksum = get_hash(self.file)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Function image associated function key {self.function.key}"

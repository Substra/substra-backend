from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from rest_framework import serializers

from substrapp.utils import raise_if_path_traversal
from substrapp.utils import safezip
from substrapp.utils import tarsafe


@deconstructible
class FileValidator(object):
    error_messages = {
        "open": "Cannot handle this file object.",
        "compressed": "Ensure this file is an archive (zip or tar.* compressed file).",
        "docker": "Ensure your archive contains a Dockerfile.",
        "file": "Ensure your archive contains at least one python file.",
        "traversal": "Ensure your archive does not contain traversal filenames (e.g. filename with `..` inside)",
    }

    def validate_archive(self, files):
        if "Dockerfile" not in files:
            raise ValidationError(self.error_messages["docker"])

        if len(files) < 2:
            raise ValidationError(self.error_messages["file"])

        try:
            raise_if_path_traversal(files, "./")
        except Exception:
            raise ValidationError(self.error_messages["traversal"])

    def __call__(self, data):
        archive = None
        try:
            data.file.seek(0)
        except Exception:
            raise ValidationError(self.error_messages["open"])
        else:
            try:
                archive = tarsafe.open(fileobj=data.file)
            except tarsafe.TarError:
                if not safezip.is_zipfile(data.file):
                    raise ValidationError(self.error_messages["compressed"])

                archive = safezip.ZipFile(file=data.file)
                self.validate_archive(archive.namelist())
            else:
                self.validate_archive(archive.getnames())
            finally:
                data.file.seek(0)

                if archive:
                    archive.close()
                else:
                    raise ValidationError(self.error_messages["open"])


class FileSizeValidator(object):
    """Validate that file does not exceed maximum allowed size"""

    def __call__(self, value):
        if value.size > settings.DATA_UPLOAD_MAX_SIZE:
            raise ValidationError("File too large")


class PermissionsSerializer(serializers.Serializer):
    public = serializers.BooleanField()
    authorized_ids = serializers.ListField(child=serializers.CharField())


class PrivatePermissionsSerializer(serializers.Serializer):
    authorized_ids = serializers.ListField(child=serializers.CharField())

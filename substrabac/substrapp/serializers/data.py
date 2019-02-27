import tarfile
import zipfile

from django.core.exceptions import ValidationError
from rest_framework import serializers

from substrapp.models import Data


from django.utils.deconstruct import deconstructible


@deconstructible
class FileValidator(object):
    error_messages = {
        'open': ("Cannot handle this file object."),
        'compressed': ("Ensure this file is an archive (zip or tar.* compressed file)."),
    }

    def __call__(self, data):

        try:
            data.file.seek(0)
        except:
            raise ValidationError(self.error_messages['open'])
        else:
            try:
                # is tarfile?
                archive = tarfile.open(fileobj=data.file)
            except tarfile.TarError:
                # is zipfile?
                if not zipfile.is_zipfile(data.file):
                    raise ValidationError(self.error_messages['compressed'])
            else:
                archive.close()


class DataSerializer(serializers.ModelSerializer):
    file = serializers.FileField(validators=[FileValidator()])

    class Meta:
        model = Data
        fields = '__all__'

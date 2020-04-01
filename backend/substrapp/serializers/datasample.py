import tarfile
import traceback
import zipfile

from django.core.exceptions import ValidationError
from django.core.files import File
from rest_framework import serializers
from rest_framework.serializers import raise_errors_on_nested_writes
from rest_framework.utils import model_meta

from substrapp.models import DataSample
from substrapp.utils import raise_if_path_traversal

from django.utils.deconstruct import deconstructible


@deconstructible
class FileValidator(object):
    error_messages = {
        'open': ("Cannot handle this file object."),
        'compressed': ("Ensure this file is an archive (zip or tar.* compressed file)."),
        'file': ("Ensure your archive contains at least one file."),
        'traversal': ("Ensure your archive does not contain traversal filenames (e.g. filename with `..` inside)"),
    }

    def validate_archive(self, files):
        if not len(files):
            raise ValidationError(self.error_messages['file'])
        try:
            raise_if_path_traversal(files, './')
        except Exception:
            raise ValidationError(self.error_messages['traversal'])

    def __call__(self, data):

        archive = None

        try:
            data.file.seek(0)
        except Exception:
            raise ValidationError(self.error_messages['open'])
        else:
            try:
                # is tarfile?
                archive = tarfile.open(fileobj=data.file)
            except tarfile.TarError:
                # is zipfile?
                if not zipfile.is_zipfile(data.file):
                    raise ValidationError(self.error_messages['compressed'])

                archive = zipfile.ZipFile(file=data.file)
                self.validate_archive(archive.namelist())
            else:
                self.validate_archive(archive.getnames())
            finally:
                data.file.seek(0)

                if archive:
                    archive.close()
                else:
                    raise ValidationError(self.error_messages['open'])


class DataSampleSerializer(serializers.ModelSerializer):
    validated = serializers.HiddenField(default=False)
    path = serializers.CharField(default='', max_length=8192, required=False)
    file = serializers.FileField(validators=[FileValidator()], required=False)

    class Meta:
        model = DataSample
        fields = '__all__'

    def create(self, validated_data):
        raise_errors_on_nested_writes('create', self, validated_data)

        ModelClass = self.Meta.model   # noqa: N806

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)

        # if path is empty and file is a InMemoryUploadedFile, switch it
        # pre_save method will uncompress the archive present in file and return a correct path
        if 'file' in validated_data and isinstance(validated_data['file'], File) and validated_data['path'] == '':
            validated_data['path'] = validated_data['file']
            del validated_data['file']

        try:
            instance = ModelClass.objects.create(**validated_data)
        except TypeError:
            tb = traceback.format_exc()
            msg = (
                'Got a `TypeError` when calling `%s.objects.create()`. '
                'This may be because you have a writable field on the '
                'serializer class that is not a valid argument to '
                '`%s.objects.create()`. You may need to make the field '
                'read-only, or override the %s.create() method to handle '
                'this correctly.\nOriginal exception was:\n %s' %
                (
                    ModelClass.__name__,
                    ModelClass.__name__,
                    self.__class__.__name__,
                    tb
                )
            )
            raise TypeError(msg)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                field = getattr(instance, field_name)
                field.set(value)

        return instance

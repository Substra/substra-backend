from rest_framework import serializers

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import DataManager
from substrapp.serializers.utils import FileSizeValidator


class DataManagerSerializer(DynamicFieldsModelSerializer):
    data_opener = serializers.FileField(validators=[FileSizeValidator()])
    description = serializers.FileField(validators=[FileSizeValidator()])

    class Meta:
        model = DataManager
        fields = "__all__"

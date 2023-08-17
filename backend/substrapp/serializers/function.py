from rest_framework import serializers

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Function
from substrapp.models import FunctionImage
from substrapp.serializers.utils import FileSizeValidator
from substrapp.serializers.utils import FileValidator


class FunctionSerializer(DynamicFieldsModelSerializer):
    file = serializers.FileField(validators=[FileValidator(), FileSizeValidator()])

    class Meta:
        model = Function
        fields = "__all__"

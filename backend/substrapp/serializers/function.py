from rest_framework import serializers

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Function
from substrapp.serializers.utils import FileSizeValidator
from substrapp.serializers.utils import SubstraFunctionArchiveValidator


class FunctionSerializer(DynamicFieldsModelSerializer):
    file = serializers.FileField(validators=[SubstraFunctionArchiveValidator(), FileSizeValidator()])

    class Meta:
        model = Function
        fields = "__all__"

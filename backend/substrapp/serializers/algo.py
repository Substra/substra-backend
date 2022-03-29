from rest_framework import serializers

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Algo
from substrapp.serializers.utils import FileSizeValidator
from substrapp.serializers.utils import FileValidator


class AlgoSerializer(DynamicFieldsModelSerializer):
    file = serializers.FileField(validators=[FileValidator(), FileSizeValidator()])

    class Meta:
        model = Algo
        fields = "__all__"

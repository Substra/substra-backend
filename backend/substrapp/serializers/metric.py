from rest_framework import serializers

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Metric
from substrapp.serializers.utils import FileSizeValidator
from substrapp.serializers.utils import FileValidator


class MetricSerializer(DynamicFieldsModelSerializer):
    address = serializers.FileField(validators=[FileValidator(), FileSizeValidator()])

    class Meta:
        model = Metric
        fields = "__all__"

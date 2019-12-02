from rest_framework import serializers

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import AggregateAlgo
from substrapp.serializers.utils import FileValidator


class AggregateAlgoSerializer(DynamicFieldsModelSerializer):
    file = serializers.FileField(validators=[FileValidator()])

    class Meta:
        model = AggregateAlgo
        fields = '__all__'

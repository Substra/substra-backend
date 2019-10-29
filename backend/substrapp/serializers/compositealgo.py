from rest_framework import serializers

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import CompositeAlgo
from substrapp.serializers.utils import FileValidator


class CompositeAlgoSerializer(DynamicFieldsModelSerializer):
    file = serializers.FileField(validators=[FileValidator()])

    class Meta:
        model = CompositeAlgo
        fields = '__all__'

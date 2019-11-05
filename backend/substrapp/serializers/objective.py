from rest_framework import serializers

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Objective

from substrapp.serializers.utils import FileValidator


class ObjectiveSerializer(DynamicFieldsModelSerializer):
    metrics = serializers.FileField(validators=[FileValidator()])

    class Meta:
        model = Objective
        fields = '__all__'

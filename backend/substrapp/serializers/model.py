from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Model


class ModelSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Model
        fields = '__all__'

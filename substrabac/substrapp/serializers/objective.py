from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Objective


class ObjectiveSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Objective
        fields = '__all__'

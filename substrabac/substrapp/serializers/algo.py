from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Algo


class AlgoSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Algo
        fields = '__all__'

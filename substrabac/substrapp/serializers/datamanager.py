from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import DataManager


class DataManagerSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = DataManager
        fields = '__all__'

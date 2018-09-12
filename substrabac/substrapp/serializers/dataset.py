from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Dataset


class DatasetSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Dataset
        fields = '__all__'

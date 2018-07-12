from rest_framework import serializers

from substrapp.models import Dataset


class DatasetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dataset
        fields = '__all__'

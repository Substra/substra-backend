from rest_framework import serializers

from substrapp.models import Data


class DataSerializer(serializers.ModelSerializer):

    class Meta:
        model = Data
        fields = '__all__'

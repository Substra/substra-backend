from rest_framework import serializers

from substrapp.models import Model


class ModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Model
        fields = '__all__'

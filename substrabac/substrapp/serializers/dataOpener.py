from rest_framework import serializers

from substrapp.models import DataOpener


class DataOpenerSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataOpener
        fields = '__all__'

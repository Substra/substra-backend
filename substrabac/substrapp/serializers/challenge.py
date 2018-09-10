from rest_framework import serializers

from libs.serializers import DynamicFieldsModelSerializer
from substrapp.models import Challenge


class ChallengeSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Challenge
        fields = '__all__'

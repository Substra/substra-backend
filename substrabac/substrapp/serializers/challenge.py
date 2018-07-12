from rest_framework import serializers

from substrapp.models import Challenge


class ChallengeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Challenge
        fields = '__all__'

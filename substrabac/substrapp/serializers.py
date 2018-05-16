from rest_framework import serializers
from .models import Problem, DataOpener, Data


class ProblemSerializer(serializers.ModelSerializer):
    test_data = serializers.ListField(child=serializers.CharField(
        min_length=69, max_length=69), min_length=1, max_length=None)
    name = serializers.CharField(min_length=1, max_length=60)

    class Meta:
        model = Problem
        fields = '__all__'

    # def create(self, validated_data):
    #     Problem.objects.create(description=validated_data["description"],
    #                            metrics=validated_data["metrics"])
    #     

    # def update(self, instance, validated_data):

    

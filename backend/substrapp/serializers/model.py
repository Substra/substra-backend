from rest_framework import serializers
from rest_framework.fields import IntegerField


class OrchestratorModelSerializer(serializers.Serializer):
    key = serializers.UUIDField()
    category = IntegerField(min_value=0, max_value=3)
    compute_task_key = serializers.UUIDField()

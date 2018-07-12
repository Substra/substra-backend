from rest_framework import serializers, status


class LedgerModelSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=60)

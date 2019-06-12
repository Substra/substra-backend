from rest_framework import serializers


class LedgerModelSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=60)

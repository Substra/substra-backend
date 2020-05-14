from rest_framework import serializers


class PermissionsSerializer(serializers.Serializer):
    public = serializers.BooleanField()
    authorized_ids = serializers.ListField(child=serializers.CharField())


class PrivatePermissionsSerializer(serializers.Serializer):
    authorized_ids = serializers.ListField(child=serializers.CharField())

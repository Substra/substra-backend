from rest_framework import serializers

from substrapp.models import DataSample
from substrapp.serializers.utils import FileSizeValidator


class DataSampleSerializer(serializers.ModelSerializer):
    # write_only because sensitive data should never be served by the API.
    file = serializers.FileField(write_only=True, required=False, validators=[FileSizeValidator()])
    # servermedias
    path = serializers.CharField(max_length=8192, required=False)

    class Meta:
        model = DataSample
        fields = "__all__"

    def validate(self, data):
        if bool(data.get("file")) == bool(data.get("path")):
            raise serializers.ValidationError("Expect either file or path.")
        return super().validate(data)

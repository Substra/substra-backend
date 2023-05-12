from datetime import timezone

from rest_framework import serializers

from users.models.token import BearerToken
from users.models.token import ImplicitBearerToken


class BearerTokenSerializer(serializers.ModelSerializer):
    expires_at = serializers.DateTimeField(default_timezone=timezone.utc, allow_null=True)
    created_at = serializers.DateTimeField(default_timezone=timezone.utc, source="created", read_only=True)
    token = serializers.CharField(source="key", read_only=True)

    class Meta:
        model = BearerToken
        fields = ["id", "note", "expires_at", "created_at", "token"]
        read_only_fields = ["id"]

    def __init__(self, *args, **kwargs):
        include_payload = kwargs.pop("include_payload", False)
        if not include_payload:
            del self.fields["token"]
        super().__init__(*args, **kwargs)


class ImplicitBearerTokenSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(default_timezone=timezone.utc, source="created", read_only=True)
    token = serializers.CharField(source="key", read_only=True)

    class Meta:
        model = ImplicitBearerToken
        fields = ["expires_at", "created_at", "token"]

    def __init__(self, *args, **kwargs):
        include_payload = kwargs.pop("include_payload", False)
        if not include_payload:
            del self.fields["token"]
        super().__init__(*args, **kwargs)

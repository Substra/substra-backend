from django.urls import reverse
from rest_framework import serializers

from api.models import ComputeTask
from api.models import Model
from api.serializers.utils import SafeSerializerMixin
from api.serializers.utils import get_channel_choices
from api.serializers.utils import make_addressable_serializer
from api.serializers.utils import make_download_process_permission_serializer


class ModelSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    compute_task_key = serializers.PrimaryKeyRelatedField(
        queryset=ComputeTask.objects.all(), source="compute_task", pk_field=serializers.UUIDField(format="hex_verbose")
    )
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    address = make_addressable_serializer("model")(source="*", required=False)
    permissions = make_download_process_permission_serializer()(source="*")

    class Meta:
        model = Model
        fields = [
            "address",
            "category",
            "channel",
            "compute_task_key",
            "creation_date",
            "key",
            "owner",
            "permissions",
        ]

    def to_representation(self, instance):
        model = super().to_representation(instance)
        request = self.context.get("request")
        if model["address"]["storage_address"] is None:
            # disabled model
            model["address"] = None
        elif request:
            if "address" in model and model["address"]:
                model["address"]["storage_address"] = request.build_absolute_uri(
                    reverse("api:model-file", args=[model["key"]])
                )
        return model

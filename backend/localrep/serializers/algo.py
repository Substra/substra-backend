from rest_framework import serializers

import orchestrator.algo_pb2 as algo_pb2
from localrep.models import Algo
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from localrep.serializers.utils import make_addressable_serializer
from localrep.serializers.utils import make_download_process_permission_serializer


class CategoryField(serializers.Field):
    def to_representation(self, value):
        return algo_pb2.AlgoCategory.Name(value)

    def to_internal_value(self, value):
        return algo_pb2.AlgoCategory.Value(value)


class AlgoSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    algorithm = make_addressable_serializer("algorithm")(source="*")
    category = CategoryField()
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)
    description = make_addressable_serializer("description")(source="*")
    permissions = make_download_process_permission_serializer()(source="*")

    class Meta:
        model = Algo
        fields = [
            "algorithm",
            "category",
            "channel",
            "creation_date",
            "description",
            "key",
            "metadata",
            "name",
            "owner",
            "permissions",
        ]

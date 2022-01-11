from rest_framework import serializers

import orchestrator.algo_pb2 as algo_pb2
from localrep.models import Algo
from localrep.serializers.utils import PermissionsSerializer
from localrep.serializers.utils import SafeSerializerMixin
from localrep.serializers.utils import get_channel_choices
from localrep.serializers.utils import make_addressable_serializer


class CategoryField(serializers.Field):
    def to_representation(self, value):
        return algo_pb2.AlgoCategory.Name(value)

    def to_internal_value(self, value):
        return algo_pb2.AlgoCategory.Value(value)


class AlgoSerializer(serializers.ModelSerializer, SafeSerializerMixin):
    category = CategoryField()
    description = make_addressable_serializer("description")(source="*")
    algorithm = make_addressable_serializer("algorithm")(source="*")
    permissions = PermissionsSerializer(source="*")
    channel = serializers.ChoiceField(choices=get_channel_choices(), write_only=True)

    class Meta:
        model = Algo
        fields = [
            "key",
            "name",
            "category",
            "owner",
            "creation_date",
            "metadata",
            "description",
            "algorithm",
            "permissions",
            "channel",
        ]

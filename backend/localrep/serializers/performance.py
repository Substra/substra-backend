from rest_framework import serializers

from localrep.models import Performance
from localrep.serializers.utils import SafeSerializerMixin


class PerformanceSerializer(serializers.ModelSerializer, SafeSerializerMixin):

    # overwritte primary key field for the SafeSerializerMixin check
    # the unique constraint for compute_task_key + metric_key in the model
    # ensures no dupplicates are created
    primary_key_name = "id"

    class Meta:
        model = Performance
        fields = ["compute_task_key", "metric_key", "performance_value", "creation_date", "channel"]

from typing import Union

from django.utils.duration import duration_string
from rest_framework import serializers

from api.models import ComputeTask
from api.models import TaskProfiling
from api.models.task_profiling import ProfilingStep


class ProfilingStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilingStep
        fields = [
            "step",
            "duration",
        ]


class TaskProfilingSerializer(serializers.ModelSerializer):
    compute_task_key = serializers.PrimaryKeyRelatedField(
        queryset=ComputeTask.objects.all(), source="compute_task", pk_field=serializers.UUIDField(format="hex_verbose")
    )
    task_duration = serializers.SerializerMethodField()
    execution_rundown = ProfilingStepSerializer(many=True, required=False)

    class Meta:
        model = TaskProfiling
        fields = [
            "compute_task_key",
            "task_duration",
            "execution_rundown",
        ]

    def get_task_duration(self, obj: TaskProfiling) -> Union[str, None]:
        if obj.compute_task.start_date is not None and obj.compute_task.end_date is not None:
            duration = obj.compute_task.end_date - obj.compute_task.start_date
            return duration_string(duration)
        else:
            return None

    def create(self, data):
        task_profiling, created = TaskProfiling.objects.update_or_create(**data)
        return task_profiling

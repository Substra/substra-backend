from typing import Union

from django.utils.duration import duration_microseconds
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["duration"] = duration_microseconds(instance.duration)
        return representation


class TaskProfilingSerializer(serializers.ModelSerializer):
    compute_task_key = serializers.PrimaryKeyRelatedField(
        queryset=ComputeTask.objects.all(), source="compute_task", pk_field=serializers.UUIDField(format="hex_verbose")
    )
    task_duration = serializers.SerializerMethodField()
    execution_rundown = serializers.SerializerMethodField("get_steps")

    class Meta:
        model = TaskProfiling
        fields = [
            "compute_task_key",
            "task_duration",
            "execution_rundown",
        ]

    def get_task_duration(self, obj: TaskProfiling) -> Union[str, None]:
        if obj.creation_date is not None and obj.compute_task.end_date is not None:
            duration = obj.compute_task.end_date - obj.creation_date
            return duration_microseconds(duration)
        else:
            return None

    # Had to add a function for excluding steps that should not be displayed from previous measurement because
    # nested fields does not use `get_queryset` as defined in their models
    def get_steps(self, task_profiling):
        steps = ProfilingStep.objects.filter(compute_task_profile=task_profiling).exclude(step="build_image")
        serializer = ProfilingStepSerializer(instance=steps, many=True, required=False)
        return serializer.data

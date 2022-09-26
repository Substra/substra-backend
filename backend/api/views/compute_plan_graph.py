import structlog
from django.db.models import Field
from django.db.models.expressions import F
from rest_framework import status
from rest_framework.decorators import api_view

from api.models import ComputeTask, Algo, AlgoOutput, AlgoInput, ComputeTaskInput
from api.views.sql_utils import Any
from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from api.views.utils import validate_key

from api.serializers.utils import SafeSerializerMixin

# register lookup where used as a workaround of import not used error from Flake8
Field.register_lookup(Any)

logger = structlog.get_logger(__name__)

MAX_TASKS_DISPLAYED = 1000

from rest_framework import serializers


class AlgoInputSerializerForGraph(serializers.ModelSerializer, SafeSerializerMixin):
    id = serializers.CharField(source="identifier")

    class Meta:
        model = AlgoInput
        fields = [
            "id",
            "kind",
        ]


class AlgoOutputSerializerForGraph(serializers.ModelSerializer, SafeSerializerMixin):
    id = serializers.CharField(source="identifier")

    class Meta:
        model = AlgoOutput
        fields = [
            "id",
            "kind",
        ]


class AlgoSerializerForGraph(serializers.ModelSerializer, SafeSerializerMixin):
    inputs = AlgoInputSerializerForGraph(many=True)
    outputs = AlgoOutputSerializerForGraph(many=True)

    class Meta:
        model = Algo
        fields = [
            "inputs",
            "outputs",
        ]


class TaskSerializerForGraph(serializers.ModelSerializer, SafeSerializerMixin):

    algo = AlgoSerializerForGraph()

    class Meta:
        model = ComputeTask
        fields = ["key", "rank", "worker", "status", "category", "algo"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["inputs"] = data["algo"]["inputs"]
        data["outputs"] = data["algo"]["outputs"]
        del data["algo"]
        return data


@api_view(["GET"])
def get_cp_graph(request, compute_plan_pk):
    """Return a workflow graph for each task of the computeplan"""
    validate_key(compute_plan_pk)

    tasks_qs = ComputeTask.objects.filter(compute_plan__key=compute_plan_pk, channel=get_channel_name(request))
    tasks = TaskSerializerForGraph(tasks_qs, many=True).data

    # Set a task limitation for performances issues
    if len(tasks) > MAX_TASKS_DISPLAYED:
        return ApiResponse(
            data={"message": f"Cannot build workflow graph for more than {MAX_TASKS_DISPLAYED} tasks."},
            status=status.HTTP_403_FORBIDDEN,
        )

    edges_qs = ComputeTaskInput.objects.filter(
        task__compute_plan__key=compute_plan_pk, channel=get_channel_name(request)
    ).exclude(parent_task_key__isnull=True, parent_task_output_identifier__isnull=True)

    edges = edges_qs.annotate(
        source_task_key=F("parent_task_key"),
        source_output_name=F("parent_task_output_identifier"),
        target_task_key=F("task__key"),
        target_input_name=F("identifier"),
    ).values("source_task_key", "source_output_name", "target_task_key", "target_input_name")

    return ApiResponse(
        data={
            "tasks": tasks,
            "edges": edges,
        },
        status=status.HTTP_200_OK,
    )

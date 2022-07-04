import structlog
from rest_framework import mixins
from rest_framework import status
from rest_framework.viewsets import GenericViewSet

from localrep.models import ComputeTask as ComputeTaskRep
from localrep.serializers import CPWorkflowTasksSerializer
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


def _compute_task_edges(task, tasks_keys_dict):
    """Computing source output and target input"""
    edges = []
    for source_task_key in task["source_task_keys"]:
        source_task_category = tasks_keys_dict[str(source_task_key)]["category"]

        # Compute the source_output_name
        if source_task_category == "TASK_AGGREGATE":
            source_output_name = "out/model"
        elif source_task_category == "TASK_TRAIN":
            source_output_name = "out/model"
        elif source_task_category == "TASK_COMPOSITE":
            source_output_name = "out/trunk_model" if task["category"] == "TASK_AGGREGATE" else "out/head_model"
        else:
            raise Exception(
                (
                    "Failed to build CP workflow graph. Could not build an edge for: "
                    f"task {task['key']} has task {source_task_category} in its parents list."
                )
            )

        # Compute the target_input_name
        if task["category"] == "TASK_TEST":
            target_input_name = "in/tested_model"
        elif task["category"] == "TASK_TRAIN":
            target_input_name = "in/model"
        elif task["category"] == "TASK_AGGREGATE":
            target_input_name = "in/models[]"
        elif task["category"] == "TASK_COMPOSITE":
            target_input_name = "in/trunk_model" if source_task_category == "TASK_AGGREGATE" else "in/head_model"
        else:
            raise Exception(
                (
                    "Failed to build CP workflow graph. Could not build an edge for: "
                    f"task {task['key']} has a category {task['category']}."
                )
            )

        # Populate edges
        edges.append(
            {
                "source_task_key": source_task_key,
                "target_task_key": task["key"],
                "source_output_name": source_output_name,
                "target_input_name": target_input_name,
            }
        )

    return edges


def compute_edges(tasks):
    edges = []

    # Create a task_keys dict to fetch category
    tasks_keys_dict = dict((task["key"], task) for task in tasks)

    for task in tasks:
        edges += _compute_task_edges(task, tasks_keys_dict)

    return edges


class CPWorkflowGraphViewSet(mixins.ListModelMixin, GenericViewSet):
    def get_queryset(self):
        compute_plan_key = self.kwargs.get("compute_plan_pk")
        validate_key(compute_plan_key)

        queryset = ComputeTaskRep.objects.filter(
            compute_plan__key=compute_plan_key, channel=get_channel_name(self.request)
        )
        return queryset

    def list(self, request, compute_plan_pk):
        """Return a workflow graph for each task of the computeplan"""
        # Limitation to display at most 300 tasks for performances
        if self.get_queryset().count() > 300:
            return ApiResponse(
                data={"message": "Cannot build workflow graph for more than 300 tasks."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tasks_serializer = CPWorkflowTasksSerializer(self.get_queryset(), many=True)
        tasks = tasks_serializer.data

        return ApiResponse(
            {
                "tasks": tasks,
                "edges": compute_edges(tasks),
            }
        )

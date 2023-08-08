import structlog
from django.contrib.postgres.aggregates import JSONBAgg
from django.db.models import Field
from django.db.models import Func
from django.db.models import OuterRef
from django.db.models import Subquery
from django.db.models.expressions import F
from django.db.models.expressions import Value
from rest_framework import status
from rest_framework.decorators import api_view

from api.models import ComputeTask
from api.models import ComputeTaskInput
from api.views.sql_utils import Any
from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from api.views.utils import validate_key

# register lookup where used as a workaround of import not used error from Flake8
Field.register_lookup(Any)

logger = structlog.get_logger(__name__)

MAX_TASKS_DISPLAYED = 5000


class JsonbBuildObj(Func):
    function = "jsonb_build_object"


@api_view(["GET"])
def get_cp_graph(request, compute_plan_pk):
    """Return a workflow graph for each task of the computeplan.
    As this view is used to build a graph and therefore cannot be paginated yet,
    it does not use any serialization for performance optimization"""
    validate_key(compute_plan_pk)

    outputs = (
        ComputeTask.objects.filter(key=OuterRef("pk"))
        .annotate(
            outputs_specs=JSONBAgg(
                JsonbBuildObj(
                    Value("identifier"), F("function__outputs__identifier"), Value("kind"), "function__outputs__kind"
                )
            ),
        )
        .values("outputs_specs")
    )

    inputs = (
        ComputeTask.objects.filter(key=OuterRef("pk"))
        .annotate(
            inputs_specs=JSONBAgg(
                JsonbBuildObj(
                    Value("identifier"), F("function__inputs__identifier"), Value("kind"), "function__inputs__kind"
                )
            ),
        )
        .values("inputs_specs")
    )

    tasks = (
        ComputeTask.objects.filter(compute_plan__key=compute_plan_pk, channel=get_channel_name(request))
        # fetch_related not needed because annotate already performs a JOIN
        .annotate(
            inputs_specs=Subquery(inputs), outputs_specs=Subquery(outputs), function_name=F("function__name")
        ).values("key", "rank", "function_name", "worker", "status", "inputs_specs", "outputs_specs")
    )

    # Set a task limitation for performances issues
    if len(tasks) > MAX_TASKS_DISPLAYED:
        return ApiResponse(
            data={"detail": f"Cannot build workflow graph for more than {MAX_TASKS_DISPLAYED} tasks."},
            status=status.HTTP_403_FORBIDDEN,
        )

    edges_qs = ComputeTaskInput.objects.filter(
        task__compute_plan__key=compute_plan_pk, channel=get_channel_name(request)
    ).exclude(parent_task_key__isnull=True, parent_task_output_identifier__isnull=True)

    edges = edges_qs.annotate(
        source_task_key=F("parent_task_key"),
        source_output_identifier=F("parent_task_output_identifier"),
        target_task_key=F("task__key"),
        target_input_identifier=F("identifier"),
    ).values("source_task_key", "source_output_identifier", "target_task_key", "target_input_identifier")

    return ApiResponse(
        data={
            "tasks": tasks,
            "edges": edges,
        },
        status=status.HTTP_200_OK,
    )

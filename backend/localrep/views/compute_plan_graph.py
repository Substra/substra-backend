import structlog
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import Field
from django.db.models import Func
from django.db.models import OuterRef
from django.db.models.expressions import F
from rest_framework import status
from rest_framework.decorators import api_view

from localrep.models import ComputeTask as ComputeTaskRep
from localrep.views.sql_utils import Any
from localrep.views.utils import ApiResponse
from localrep.views.utils import get_channel_name
from localrep.views.utils import validate_key

# register lookup where used as a workaround of import not used error from Flake8
Field.register_lookup(Any)

logger = structlog.get_logger(__name__)

TASK_CATEGORY_INPUTS = {
    ComputeTaskRep.Category.TASK_TRAIN: ["in/model"],
    ComputeTaskRep.Category.TASK_TEST: ["in/predictions"],
    ComputeTaskRep.Category.TASK_COMPOSITE: ["in/head_model", "in/trunk_model"],
    ComputeTaskRep.Category.TASK_AGGREGATE: ["in/models[]"],
    ComputeTaskRep.Category.TASK_PREDICT: ["in/tested_model"],
}

TASK_CATEGORY_OUTPUTS = {
    ComputeTaskRep.Category.TASK_TRAIN: ["out/model"],
    ComputeTaskRep.Category.TASK_TEST: [],
    ComputeTaskRep.Category.TASK_COMPOSITE: ["out/head_model", "out/trunk_model"],
    ComputeTaskRep.Category.TASK_AGGREGATE: ["out/model"],
    ComputeTaskRep.Category.TASK_PREDICT: ["out/predictions"],
}

MAX_TASKS_DISPLAYED = 1000


def _get_task_inputs(category):
    return TASK_CATEGORY_INPUTS.get(category, [])


def _get_task_outputs(category):
    return TASK_CATEGORY_OUTPUTS.get(category, [])


def _get_target_input(edge):
    target_category = edge.get("target_task_category")
    inputs = TASK_CATEGORY_INPUTS.get(target_category, [])
    if TASK_CATEGORY_INPUTS.get(target_category) is None:
        raise Exception(
            (
                "Failed to build CP workflow graph. Could not build an edge for: "
                f"task {edge['target_task_key']} has a category {target_category}."
            )
        )
    if (
        target_category == ComputeTaskRep.Category.TASK_COMPOSITE
        and edge.get("source_task_category") == ComputeTaskRep.Category.TASK_AGGREGATE
    ):
        input = inputs[1]
    else:
        input = inputs[0]

    return input


def _get_source_output(edge):
    source_category = edge.get("source_task_category")
    outputs = TASK_CATEGORY_OUTPUTS.get(source_category, [])
    if TASK_CATEGORY_OUTPUTS.get(source_category) is None:
        raise Exception(
            (
                "Failed to build CP workflow graph. Could not build an edge for: "
                f"task {edge['target_task_key']} has a category {source_category}."
            )
        )
    if (
        source_category == ComputeTaskRep.Category.TASK_COMPOSITE
        and edge.get("target_task_category") == ComputeTaskRep.Category.TASK_AGGREGATE
    ):
        output = outputs[1]
    else:
        output = outputs[0]

    return output


@api_view(["GET"])
def get_cp_graph(request, compute_plan_pk):
    """Return a workflow graph for each task of the computeplan"""
    validate_key(compute_plan_pk)

    tasks = ComputeTaskRep.objects.filter(compute_plan__key=compute_plan_pk, channel=get_channel_name(request)).values(
        "key",
        "rank",
        "worker",
        "status",
        "category",
    )

    # Set a task limitation for performances issues
    if tasks.count() > MAX_TASKS_DISPLAYED:
        return ApiResponse(
            data={"message": f"Cannot build workflow graph for more than {MAX_TASKS_DISPLAYED} tasks."},
            status=status.HTTP_403_FORBIDDEN,
        )

    for task in tasks:
        task["inputs"] = _get_task_inputs(task.get("category"))
        task["outputs"] = _get_task_outputs(task.get("category"))

    parent_tasks = ComputeTaskRep.objects.filter(key__any=OuterRef("parent_tasks"))

    edges = (
        ComputeTaskRep.objects.filter(compute_plan__key=compute_plan_pk, channel=get_channel_name(request))
        .annotate(
            source_task_key=Func(ArraySubquery(parent_tasks.values("key")), function="unnest"),
            source_task_category=Func(ArraySubquery(parent_tasks.values("category")), function="unnest"),
            target_task_key=F("key"),
            target_task_category=F("category"),
        )
        .values("source_task_key", "target_task_key", "source_task_category", "target_task_category")
    )

    for edge in edges:
        edge["source_output_name"] = _get_source_output(edge)
        edge["target_input_name"] = _get_target_input(edge)

    return ApiResponse(
        data={
            "tasks": tasks,
            "edges": edges,
        },
        status=status.HTTP_200_OK,
    )

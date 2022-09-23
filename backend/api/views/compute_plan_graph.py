import structlog
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import Field
from django.db.models import Func
from django.db.models import OuterRef
from django.db.models.expressions import F
from rest_framework import status
from rest_framework.decorators import api_view

from api.models import ComputeTask
from api.views.sql_utils import Any
from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from api.views.utils import validate_key

# register lookup where used as a workaround of import not used error from Flake8
Field.register_lookup(Any)

logger = structlog.get_logger(__name__)

TASK_CATEGORY_INPUTS = {
    ComputeTask.Category.TASK_TRAIN: [{"id": "in/model", "kind": "model"}],
    ComputeTask.Category.TASK_TEST: [{"id": "in/predictions", "kind": "model"}],
    ComputeTask.Category.TASK_COMPOSITE: [
        {"id": "in/head_model", "kind": "model"},
        {"id": "in/trunk_model", "kind": "model"},
    ],
    ComputeTask.Category.TASK_AGGREGATE: [{"id": "in/models[]", "kind": "model"}],
    ComputeTask.Category.TASK_PREDICT: [{"id": "in/tested_model", "kind": "model"}],
}

TASK_CATEGORY_OUTPUTS = {
    ComputeTask.Category.TASK_TRAIN: [{"id": "out/model", "kind": "model"}],
    ComputeTask.Category.TASK_TEST: [{"id": "out/perf", "kind": "performance"}],
    ComputeTask.Category.TASK_COMPOSITE: [
        {"id": "out/head_model", "kind": "model"},
        {"id": "out/trunk_model", "kind": "model"},
    ],
    ComputeTask.Category.TASK_AGGREGATE: [{"id": "out/model", "kind": "model"}],
    ComputeTask.Category.TASK_PREDICT: [{"id": "out/predictions", "kind": "model"}],
}

MAX_TASKS_DISPLAYED = 1000


def _get_task_inputs(category):
    return TASK_CATEGORY_INPUTS.get(category, [])


def _get_task_outputs(category):
    return TASK_CATEGORY_OUTPUTS.get(category, [])


def _get_target_input(edge):
    target_category = edge.get("target_task_category")
    inputs = [input["id"] for input in TASK_CATEGORY_INPUTS.get(target_category, [])]
    if TASK_CATEGORY_INPUTS.get(target_category) is None:
        raise Exception(
            (
                "Failed to build CP workflow graph. Could not build an edge for: "
                f"task {edge['target_task_key']} has a category {target_category}."
            )
        )
    if (
        target_category == ComputeTask.Category.TASK_COMPOSITE
        and edge.get("source_task_category") == ComputeTask.Category.TASK_AGGREGATE
    ):
        input = inputs[1]
    else:
        input = inputs[0]

    return input


def _get_source_output(edge):
    source_category = edge.get("source_task_category")
    outputs = [output["id"] for output in TASK_CATEGORY_OUTPUTS.get(source_category, [])]
    if TASK_CATEGORY_OUTPUTS.get(source_category) is None:
        raise Exception(
            (
                "Failed to build CP workflow graph. Could not build an edge for: "
                f"task {edge['target_task_key']} has a category {source_category}."
            )
        )
    if (
        source_category == ComputeTask.Category.TASK_COMPOSITE
        and edge.get("target_task_category") == ComputeTask.Category.TASK_AGGREGATE
    ):
        output = outputs[1]
    else:
        output = outputs[0]

    return output


@api_view(["GET"])
def get_cp_graph(request, compute_plan_pk):
    """Return a workflow graph for each task of the computeplan"""
    validate_key(compute_plan_pk)

    tasks = ComputeTask.objects.filter(compute_plan__key=compute_plan_pk, channel=get_channel_name(request)).values(
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

    parent_tasks = ComputeTask.objects.filter(key__any=OuterRef("parent_tasks"))

    edges = (
        ComputeTask.objects.filter(compute_plan__key=compute_plan_pk, channel=get_channel_name(request))
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

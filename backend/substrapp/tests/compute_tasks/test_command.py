import json
from typing import Dict

import orchestrator.computetask_pb2 as computetask_pb2
import substrapp.tests.assets as assets
from substrapp.compute_tasks.command import _get_args
from substrapp.compute_tasks.context import Context
from substrapp.tests.common import get_compute_plan
from substrapp.tests.common import get_data_manager
from substrapp.tests.common import get_task
from substrapp.tests.common import get_task_metrics
from substrapp.tests.common import get_test_task_input_models

_CHANNEL = "mychannel"
_TASK_CATEGORY_NAME_TRAIN = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_TRAIN)
_TASK_CATEGORY_NAME_COMPOSITE = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_COMPOSITE)


def test_get_args_train_task():
    task = assets.get_train_task()
    cp = get_compute_plan(task["compute_plan_key"])
    dm = get_data_manager(task["train"]["data_manager_key"])
    in_models = get_test_task_input_models(task)

    ctx = Context(
        channel_name=_CHANNEL,
        task=task,
        task_category=computetask_pb2.TASK_TRAIN,
        task_key=task["key"],
        compute_plan=cp,
        compute_plan_key=cp["key"],
        compute_plan_tag=None,
        in_models=in_models,
        algo=task["algo"],
        metrics={},
        data_manager=dm,
        directories={},
        has_chainkeys=False,
    )

    inputs = []
    for m in get_test_task_input_models(task):
        inputs.append({"id": "models", "value": f"/substra_internal/in_models/{m['key']}"})
    inputs.append(
        {"id": "opener", "value": f"/substra_internal/openers/{task['train']['data_manager_key']}/__init__.py"}
    )
    for ds_key in task["train"]["data_sample_keys"]:
        inputs.append({"id": "datasamples", "value": f"/substra_internal/data_samples/{ds_key}"})

    outputs = [
        {"id": "model", "value": "/substra_internal/out_models/out-model"},
        {"id": "localfolder", "value": "/substra_internal/local"},
    ]

    actual = _get_args(ctx, ctx.algo.key, False)
    assert actual == [
        "train",
        "--rank",
        "0",
        "--inputs",
        f"'{json.dumps(inputs)}'",
        "--outputs",
        f"'{json.dumps(outputs)}'",
    ]


def test_get_args_composite_task():
    task = assets.get_composite_task()
    cp = get_compute_plan(task["compute_plan_key"])
    dm = get_data_manager(task["composite"]["data_manager_key"])
    in_models = get_test_task_input_models(task)

    ctx = Context(
        channel_name=_CHANNEL,
        task=task,
        task_category=computetask_pb2.TASK_COMPOSITE,
        task_key=task["key"],
        compute_plan=cp,
        compute_plan_key=cp["key"],
        compute_plan_tag=None,
        in_models=in_models,
        algo=task["algo"],
        metrics={},
        data_manager=dm,
        directories={},
        has_chainkeys=False,
    )

    inputs = []
    in_models = get_test_task_input_models(task)
    if in_models:
        inputs.append({"id": "local", "value": f"/substra_internal/in_models/{in_models[0]['key']}"})
        inputs.append({"id": "shared", "value": f"/substra_internal/in_models/{in_models[1]['key']}"})

    inputs.append(
        {"id": "opener", "value": f"/substra_internal/openers/{task['composite']['data_manager_key']}/__init__.py"}
    )

    for ds_key in task["composite"]["data_sample_keys"]:
        inputs.append({"id": "datasamples", "value": f"/substra_internal/data_samples/{ds_key}"})

    outputs = [
        {"id": "local", "value": "/substra_internal/out_models/out-head-model"},
        {"id": "shared", "value": "/substra_internal/out_models/out-model"},
        {"id": "localfolder", "value": "/substra_internal/local"},
    ]

    actual = _get_args(ctx, ctx.algo.key, False)
    assert actual == [
        "train",
        "--rank",
        "0",
        "--inputs",
        f"'{json.dumps(inputs)}'",
        "--outputs",
        f"'{json.dumps(outputs)}'",
    ]


def test_get_args_predict_train():
    task = _get_test_task_with_parent_of_type(_TASK_CATEGORY_NAME_TRAIN)
    ctx = _get_test_ctx(task)

    inputs = []
    inputs += [
        {"id": "models", "value": f"/substra_internal/in_models/{m['key']}"} for m in get_test_task_input_models(task)
    ]

    inputs.append(
        {"id": "opener", "value": f"/substra_internal/openers/{task['test']['data_manager_key']}/__init__.py"}
    )

    for ds_key in task["test"]["data_sample_keys"]:
        inputs.append({"id": "datasamples", "value": f"/substra_internal/data_samples/{ds_key}"})

    outputs = [
        {"id": "predictions", "value": "/substra_internal/pred/pred.json"},
        {"id": "localfolder", "value": "/substra_internal/local"},
    ]

    actual = _get_args(ctx, ctx.algo.key, False)
    assert actual == ["predict", "--inputs", f"'{json.dumps(inputs)}'", "--outputs", f"'{json.dumps(outputs)}'"]


def test_get_args_eval_train():
    task = _get_test_task_with_parent_of_type(_TASK_CATEGORY_NAME_TRAIN)
    metric_key = task["test"]["metric_keys"][0]
    ctx = _get_test_ctx(task)

    cmd = [
        "--input-predictions-path",
        "/substra_internal/pred/pred.json",
        "--opener-path",
        f"/substra_internal/openers/{task['test']['data_manager_key']}/__init__.py",
    ]

    cmd.append("--data-sample-paths")
    for ds_key in task["test"]["data_sample_keys"]:
        cmd.append(f"/substra_internal/data_samples/{ds_key}")

    cmd += ["--output-perf-path", f"/substra_internal/perf/{task['test']['metric_keys'][0]}-perf.json"]

    actual = _get_args(ctx, metric_key, True)
    assert actual == cmd


def test_get_args_predict_composite():
    task = _get_test_task_with_parent_of_type(_TASK_CATEGORY_NAME_COMPOSITE)
    ctx = _get_test_ctx(task)

    inputs = []

    in_models = get_test_task_input_models(task)
    inputs.append({"id": "local", "value": f"/substra_internal/in_models/{in_models[0]['key']}"})
    inputs.append({"id": "shared", "value": f"/substra_internal/in_models/{in_models[1]['key']}"})

    inputs.append(
        {"id": "opener", "value": f"/substra_internal/openers/{task['test']['data_manager_key']}/__init__.py"}
    )

    for ds_key in task["test"]["data_sample_keys"]:
        inputs.append({"id": "datasamples", "value": f"/substra_internal/data_samples/{ds_key}"})

    outputs = [
        {"id": "predictions", "value": "/substra_internal/pred/pred.json"},
        {"id": "localfolder", "value": "/substra_internal/local"},
    ]

    actual = _get_args(ctx, ctx.algo.key, False)
    assert actual == ["predict", "--inputs", f"'{json.dumps(inputs)}'", "--outputs", f"'{json.dumps(outputs)}'"]


def test_get_args_eval_composite():
    task = _get_test_task_with_parent_of_type(_TASK_CATEGORY_NAME_COMPOSITE)
    metric_key = task["test"]["metric_keys"][0]
    ctx = _get_test_ctx(task)

    cmd = [
        "--input-predictions-path",
        "/substra_internal/pred/pred.json",
        "--opener-path",
        f"/substra_internal/openers/{task['test']['data_manager_key']}/__init__.py",
    ]

    cmd.append("--data-sample-paths")
    for ds_key in task["test"]["data_sample_keys"]:
        cmd.append(f"/substra_internal/data_samples/{ds_key}")

    cmd += ["--output-perf-path", f"/substra_internal/perf/{task['test']['metric_keys'][0]}-perf.json"]

    actual = _get_args(ctx, metric_key, True)
    assert actual == cmd


def _get_test_ctx(task: Dict) -> Context:
    cp = get_compute_plan(task["compute_plan_key"])
    metrics = get_task_metrics(task)
    in_models = get_test_task_input_models(task)

    return Context(
        channel_name=_CHANNEL,
        task=task,
        task_category=computetask_pb2.TASK_TEST,
        task_key=task["key"],
        compute_plan=cp,
        compute_plan_key=cp["key"],
        compute_plan_tag=None,
        in_models=in_models,
        algo=task["algo"],
        metrics=metrics,
        data_manager=None,
        directories={},
        has_chainkeys=False,
    )


def _get_test_task_with_parent_of_type(category_name: str) -> Dict:
    for t in assets.get_test_tasks():
        if get_task(t["parent_task_keys"][0])["category"] == category_name:
            return t
    raise Exception("assets.py doesn't contain any test task with a parent of type " + category_name)

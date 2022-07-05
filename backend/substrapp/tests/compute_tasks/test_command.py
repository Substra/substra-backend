import json

from pytest_mock import MockerFixture

import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.model_pb2 as model_pb2
from substrapp.compute_tasks.command import _get_args
from substrapp.compute_tasks.context import Context
from substrapp.tests.orchestrator_factory import Orchestrator

_CHANNEL = "mychannel"


def test_get_args_train_task(mocker: MockerFixture, orchestrator: Orchestrator):
    mocker.patch("substrapp.compute_tasks.context.get_orchestrator_client", return_value=orchestrator.client)

    cp = orchestrator.create_compute_plan()
    parent_task = orchestrator.create_train_task(compute_plan_key=cp.key)
    orchestrator.create_model(compute_task_key=parent_task.key)
    train_task = orchestrator.create_train_task(compute_plan_key=cp.key, parent_task_keys=[parent_task.key])

    ctx = Context.from_task(_CHANNEL, orchestrator.client.query_task(train_task.key))

    inputs = []
    for model in orchestrator.client.get_computetask_input_models(train_task.key):
        inputs.append({"id": "models", "value": f"/substra_internal/in_models/{model['key']}"})
    inputs.append(
        {"id": "opener", "value": f"/substra_internal/openers/{train_task.train.data_manager_key}/__init__.py"}
    )
    for ds_key in train_task.train.data_sample_keys:
        inputs.append({"id": "datasamples", "value": f"/substra_internal/data_samples/{ds_key}"})

    outputs = [
        {"id": "model", "value": "/substra_internal/out_models/out-model"},
        {"id": "localfolder", "value": "/substra_internal/local"},
    ]

    actual = _get_args(ctx)
    assert actual == [
        "train",
        "--rank",
        "0",
        "--inputs",
        f"'{json.dumps(inputs)}'",
        "--outputs",
        f"'{json.dumps(outputs)}'",
    ]


def test_get_args_composite_task(mocker: MockerFixture, orchestrator: Orchestrator):
    mocker.patch("substrapp.compute_tasks.context.get_orchestrator_client", return_value=orchestrator.client)

    cp = orchestrator.create_compute_plan()
    parent_task = orchestrator.create_composite_train_task(compute_plan_key=cp.key)
    orchestrator.create_model(compute_task_key=parent_task.key, category=model_pb2.MODEL_SIMPLE)
    orchestrator.create_model(compute_task_key=parent_task.key, category=model_pb2.MODEL_HEAD)

    inputs = [
        computetask_pb2.ComputeTaskInput(
            identifier="shared",
            parent_task_output=computetask_pb2.ParentTaskOutputRef(
                output_identifier="shared", parent_task_key=parent_task.key
            ),
        ),
        computetask_pb2.ComputeTaskInput(
            identifier="local",
            parent_task_output=computetask_pb2.ParentTaskOutputRef(
                output_identifier="shared", parent_task_key=parent_task.key
            ),
        ),
    ]

    composite_task = orchestrator.create_composite_train_task(
        compute_plan_key=cp.key, parent_task_keys=[parent_task.key], inputs=inputs
    )

    ctx = Context.from_task(_CHANNEL, orchestrator.client.query_task(composite_task.key))

    inputs = []
    in_models = orchestrator.client.get_computetask_input_models(composite_task.key)
    if in_models:
        inputs.append({"id": "shared", "value": f"/substra_internal/in_models/{in_models[0]['key']}"})
        inputs.append({"id": "local", "value": f"/substra_internal/in_models/{in_models[1]['key']}"})

    inputs.append(
        {"id": "opener", "value": f"/substra_internal/openers/{composite_task.composite.data_manager_key}/__init__.py"}
    )

    for ds_key in composite_task.composite.data_sample_keys:
        inputs.append({"id": "datasamples", "value": f"/substra_internal/data_samples/{ds_key}"})

    outputs = [
        {"id": "local", "value": "/substra_internal/out_models/out-head-model"},
        {"id": "shared", "value": "/substra_internal/out_models/out-model"},
        {"id": "localfolder", "value": "/substra_internal/local"},
    ]

    actual = _get_args(ctx)
    assert actual == [
        "train",
        "--rank",
        "0",
        "--inputs",
        f"'{json.dumps(inputs)}'",
        "--outputs",
        f"'{json.dumps(outputs)}'",
    ]


def test_get_args_predict_after_train(mocker: MockerFixture, orchestrator: Orchestrator):
    mocker.patch("substrapp.compute_tasks.context.get_orchestrator_client", return_value=orchestrator.client)

    cp = orchestrator.create_compute_plan()
    parent_task = orchestrator.create_train_task(compute_plan_key=cp.key)
    orchestrator.create_model(compute_task_key=parent_task.key)

    predict_task = orchestrator.create_predict_task(compute_plan_key=cp.key, parent_task_keys=[parent_task.key])

    ctx = Context.from_task(_CHANNEL, orchestrator.client.query_task(predict_task.key))

    inputs = []
    inputs += [
        {"id": "models", "value": f"/substra_internal/in_models/{m['key']}"}
        for m in orchestrator.client.get_computetask_input_models(predict_task.key)
    ]

    inputs.append(
        {"id": "opener", "value": f"/substra_internal/openers/{predict_task.predict.data_manager_key}/__init__.py"}
    )

    for ds_key in predict_task.predict.data_sample_keys:
        inputs.append({"id": "datasamples", "value": f"/substra_internal/data_samples/{ds_key}"})

    outputs = [
        {"id": "predictions", "value": "/substra_internal/out_models/out-model"},
        {"id": "localfolder", "value": "/substra_internal/local"},
    ]

    actual = _get_args(ctx)
    assert actual == ["predict", "--inputs", f"'{json.dumps(inputs)}'", "--outputs", f"'{json.dumps(outputs)}'"]


def test_get_args_predict_after_composite(mocker: MockerFixture, orchestrator: Orchestrator):
    mocker.patch("substrapp.compute_tasks.context.get_orchestrator_client", return_value=orchestrator.client)

    cp = orchestrator.create_compute_plan()
    parent_task = orchestrator.create_composite_train_task(compute_plan_key=cp.key)
    orchestrator.create_model(compute_task_key=parent_task.key, category=model_pb2.MODEL_HEAD)
    orchestrator.create_model(compute_task_key=parent_task.key, category=model_pb2.MODEL_SIMPLE)

    predict_task = orchestrator.create_predict_task(compute_plan_key=cp.key, parent_task_keys=[parent_task.key])

    ctx = Context.from_task(_CHANNEL, orchestrator.client.query_task(predict_task.key))

    inputs = []

    in_models = orchestrator.client.get_computetask_input_models(predict_task.key)
    inputs.append({"id": "local", "value": f"/substra_internal/in_models/{in_models[0]['key']}"})
    inputs.append({"id": "shared", "value": f"/substra_internal/in_models/{in_models[1]['key']}"})

    inputs.append(
        {"id": "opener", "value": f"/substra_internal/openers/{predict_task.predict.data_manager_key}/__init__.py"}
    )

    for ds_key in predict_task.predict.data_sample_keys:
        inputs.append({"id": "datasamples", "value": f"/substra_internal/data_samples/{ds_key}"})

    outputs = [
        {"id": "predictions", "value": "/substra_internal/out_models/out-model"},
        {"id": "localfolder", "value": "/substra_internal/local"},
    ]

    actual = _get_args(ctx)
    assert actual == ["predict", "--inputs", f"'{json.dumps(inputs)}'", "--outputs", f"'{json.dumps(outputs)}'"]


def test_get_args_test_after_predict(mocker, orchestrator: Orchestrator):
    mocker.patch("substrapp.compute_tasks.context.get_orchestrator_client", return_value=orchestrator.client)

    train_task = orchestrator.create_train_task()
    orchestrator.create_model(compute_task_key=train_task.key)
    predict_task = orchestrator.create_predict_task(
        compute_plan_key=train_task.compute_plan_key, parent_task_keys=[train_task.key]
    )
    orchestrator.create_model(compute_task_key=predict_task.key)
    test_task = orchestrator.create_test_task(
        compute_plan_key=train_task.compute_plan_key, parent_task_keys=[predict_task.key]
    )

    ctx = Context.from_task(_CHANNEL, orchestrator.client.query_task(test_task.key))

    in_model = orchestrator.client.get_computetask_input_models(test_task.key)
    cmd = [
        "--input-predictions-path",
        f"/substra_internal/in_models/{in_model[0]['key']}",
        "--opener-path",
        f"/substra_internal/openers/{test_task.test.data_manager_key}/__init__.py",
        "--data-sample-paths",
    ]
    cmd.extend([f"/substra_internal/data_samples/{ds_key}" for ds_key in test_task.test.data_sample_keys])
    cmd.append("--output-perf-path")
    cmd.append(f"/substra_internal/perf/{test_task.algo.key}-perf.json")

    actual = _get_args(ctx)

    assert actual == cmd

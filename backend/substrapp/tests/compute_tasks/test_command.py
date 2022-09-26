import json

import orchestrator
import orchestrator.mock as orc_mock
from orchestrator.resources import ComputeTaskInputAsset
from substrapp.compute_tasks import context
from substrapp.compute_tasks.command import get_exec_command_args
from substrapp.compute_tasks.directories import Directories
from substrapp.tests.common import InputIdentifiers

_CHANNEL = "mychannel"


def test_get_args_train_task():
    model = orc_mock.ModelFactory()
    data_manager = orc_mock.DataManagerFactory()
    ds1 = orc_mock.DataSampleFactory()
    ds2 = orc_mock.DataSampleFactory()
    task = orc_mock.ComputeTaskFactory(
        category=orchestrator.ComputeTaskCategory.TASK_TRAIN,
        rank=0,
    )

    input_assets = [
        ComputeTaskInputAsset(identifier=InputIdentifiers.MODEL, kind=orchestrator.AssetKind.ASSET_MODEL, model=model),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.OPENER,
            kind=orchestrator.AssetKind.ASSET_DATA_MANAGER,
            data_manager=data_manager,
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.DATASAMPLES, kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, data_sample=ds1
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.DATASAMPLES, kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, data_sample=ds2
        ),
    ]

    ctx = context.Context(
        channel_name=_CHANNEL,
        task=task,
        input_assets=input_assets,
        algo=orc_mock.AlgoFactory(
            inputs={
                InputIdentifiers.MODEL: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_MODEL),
                InputIdentifiers.OPENER: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_DATA_MANAGER),
                InputIdentifiers.DATASAMPLES: orc_mock.AlgoInputFactory(
                    kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, multiple=True
                ),
            }
        ),
        has_chainkeys=False,
        compute_plan=None,
        directories=Directories(task.key),
    )
    ctx._outputs = [
        context.OutputResource(
            identifier=InputIdentifiers.MODEL,
            kind=orchestrator.AssetKind.ASSET_MODEL,
            multiple=False,
            rel_path="out_models/out-model",
        ),
    ]

    expected_inputs = [
        {"id": InputIdentifiers.MODEL, "value": f"/substra_internal/in_models/{model.key}", "multiple": False},
        {
            "id": InputIdentifiers.OPENER,
            "value": f"/substra_internal/openers/{data_manager.key}/__init__.py",
            "multiple": False,
        },
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}", "multiple": True},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}", "multiple": True},
    ]

    expected_outputs = [
        {"id": InputIdentifiers.MODEL, "value": "/substra_internal/out_models/out-model", "multiple": False},
    ]

    actual = get_exec_command_args(ctx)
    assert actual == [
        "--rank",
        "0",
        "--inputs",
        json.dumps(expected_inputs),
        "--outputs",
        json.dumps(expected_outputs),
    ]


def test_get_args_composite_task():
    shared = orc_mock.ModelFactory()
    local = orc_mock.ModelFactory()
    data_manager = orc_mock.DataManagerFactory()
    ds1 = orc_mock.DataSampleFactory()
    ds2 = orc_mock.DataSampleFactory()
    task = orc_mock.ComputeTaskFactory(
        category=orchestrator.ComputeTaskCategory.TASK_COMPOSITE,
        rank=0,
    )

    input_assets = [
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.SHARED, kind=orchestrator.AssetKind.ASSET_MODEL, model=shared
        ),
        ComputeTaskInputAsset(identifier=InputIdentifiers.LOCAL, kind=orchestrator.AssetKind.ASSET_MODEL, model=local),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.OPENER,
            kind=orchestrator.AssetKind.ASSET_DATA_MANAGER,
            data_manager=data_manager,
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.DATASAMPLES, kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, data_sample=ds1
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.DATASAMPLES, kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, data_sample=ds2
        ),
    ]

    ctx = context.Context(
        channel_name=_CHANNEL,
        task=task,
        input_assets=input_assets,
        algo=orc_mock.AlgoFactory(
            inputs={
                InputIdentifiers.SHARED: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_MODEL),
                InputIdentifiers.LOCAL: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_MODEL),
                InputIdentifiers.OPENER: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_DATA_MANAGER),
                InputIdentifiers.DATASAMPLES: orc_mock.AlgoInputFactory(
                    kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, multiple=True
                ),
            }
        ),
        has_chainkeys=False,
        compute_plan=None,
        directories=Directories(task.compute_plan_key),
    )
    ctx._outputs = [
        context.OutputResource(
            identifier=InputIdentifiers.LOCAL,
            kind=orchestrator.AssetKind.ASSET_MODEL,
            multiple=False,
            rel_path="out_models/out-head-model",
        ),
        context.OutputResource(
            identifier=InputIdentifiers.SHARED,
            kind=orchestrator.AssetKind.ASSET_MODEL,
            multiple=False,
            rel_path="out_models/out-model",
        ),
    ]

    expected_inputs = [
        {"id": InputIdentifiers.SHARED, "value": f"/substra_internal/in_models/{shared.key}", "multiple": False},
        {"id": InputIdentifiers.LOCAL, "value": f"/substra_internal/in_models/{local.key}", "multiple": False},
        {
            "id": InputIdentifiers.OPENER,
            "value": f"/substra_internal/openers/{data_manager.key}/__init__.py",
            "multiple": False,
        },
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}", "multiple": True},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}", "multiple": True},
    ]

    expected_outputs = [
        {"id": InputIdentifiers.LOCAL, "value": "/substra_internal/out_models/out-head-model", "multiple": False},
        {"id": InputIdentifiers.SHARED, "value": "/substra_internal/out_models/out-model", "multiple": False},
    ]

    actual = get_exec_command_args(ctx)
    assert actual == [
        "--rank",
        "0",
        "--inputs",
        json.dumps(expected_inputs),
        "--outputs",
        json.dumps(expected_outputs),
    ]


def test_get_args_predict_after_train():
    model = orc_mock.ModelFactory()
    data_manager = orc_mock.DataManagerFactory()
    ds1 = orc_mock.DataSampleFactory()
    ds2 = orc_mock.DataSampleFactory()
    task = orc_mock.ComputeTaskFactory(
        category=orchestrator.ComputeTaskCategory.TASK_PREDICT,
        rank=0,
    )

    input_assets = [
        ComputeTaskInputAsset(identifier=InputIdentifiers.MODEL, kind=orchestrator.AssetKind.ASSET_MODEL, model=model),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.OPENER,
            kind=orchestrator.AssetKind.ASSET_DATA_MANAGER,
            data_manager=data_manager,
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.DATASAMPLES, kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, data_sample=ds1
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.DATASAMPLES, kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, data_sample=ds2
        ),
    ]

    ctx = context.Context(
        channel_name=_CHANNEL,
        task=task,
        input_assets=input_assets,
        algo=orc_mock.AlgoFactory(
            inputs={
                InputIdentifiers.MODEL: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_MODEL),
                InputIdentifiers.OPENER: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_DATA_MANAGER),
                InputIdentifiers.DATASAMPLES: orc_mock.AlgoInputFactory(
                    kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, multiple=True
                ),
            }
        ),
        has_chainkeys=False,
        compute_plan=None,
        directories=Directories(task.compute_plan_key),
    )
    ctx._outputs = [
        context.OutputResource(
            identifier=InputIdentifiers.PREDICTIONS,
            kind=orchestrator.AssetKind.ASSET_MODEL,
            multiple=False,
            rel_path="out_models/out-model",
        ),
    ]

    expected_inputs = [
        {"id": InputIdentifiers.MODEL, "value": f"/substra_internal/in_models/{model.key}", "multiple": False},
        {
            "id": InputIdentifiers.OPENER,
            "value": f"/substra_internal/openers/{data_manager.key}/__init__.py",
            "multiple": False,
        },
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}", "multiple": True},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}", "multiple": True},
    ]

    expected_outputs = [
        {"id": InputIdentifiers.PREDICTIONS, "value": "/substra_internal/out_models/out-model", "multiple": False},
    ]

    actual = get_exec_command_args(ctx)
    assert actual == [
        "--inputs",
        json.dumps(expected_inputs),
        "--outputs",
        json.dumps(expected_outputs),
    ]


def test_get_args_predict_after_composite():
    local = orc_mock.ModelFactory()
    shared = orc_mock.ModelFactory()
    data_manager = orc_mock.DataManagerFactory()
    ds1 = orc_mock.DataSampleFactory()
    ds2 = orc_mock.DataSampleFactory()
    task = orc_mock.ComputeTaskFactory(
        category=orchestrator.ComputeTaskCategory.TASK_PREDICT,
        rank=0,
    )

    input_assets = [
        ComputeTaskInputAsset(identifier=InputIdentifiers.LOCAL, kind=orchestrator.AssetKind.ASSET_MODEL, model=local),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.SHARED, kind=orchestrator.AssetKind.ASSET_MODEL, model=shared
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.OPENER,
            kind=orchestrator.AssetKind.ASSET_DATA_MANAGER,
            data_manager=data_manager,
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.DATASAMPLES, kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, data_sample=ds1
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.DATASAMPLES, kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, data_sample=ds2
        ),
    ]

    ctx = context.Context(
        channel_name=_CHANNEL,
        task=task,
        input_assets=input_assets,
        algo=orc_mock.AlgoFactory(
            inputs={
                InputIdentifiers.SHARED: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_MODEL),
                InputIdentifiers.LOCAL: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_MODEL),
                InputIdentifiers.OPENER: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_DATA_MANAGER),
                InputIdentifiers.DATASAMPLES: orc_mock.AlgoInputFactory(
                    kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, multiple=True
                ),
            }
        ),
        has_chainkeys=False,
        compute_plan=None,
        directories=Directories(task.compute_plan_key),
    )
    ctx._outputs = [
        context.OutputResource(
            identifier=InputIdentifiers.PREDICTIONS,
            kind=orchestrator.AssetKind.ASSET_MODEL,
            multiple=False,
            rel_path="out_models/out-model",
        ),
    ]

    expected_inputs = [
        {"id": InputIdentifiers.LOCAL, "value": f"/substra_internal/in_models/{local.key}", "multiple": False},
        {"id": InputIdentifiers.SHARED, "value": f"/substra_internal/in_models/{shared.key}", "multiple": False},
        {
            "id": InputIdentifiers.OPENER,
            "value": f"/substra_internal/openers/{data_manager.key}/__init__.py",
            "multiple": False,
        },
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}", "multiple": True},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}", "multiple": True},
    ]

    expected_outputs = [
        {"id": InputIdentifiers.PREDICTIONS, "value": "/substra_internal/out_models/out-model", "multiple": False},
    ]

    actual = get_exec_command_args(ctx)
    assert actual == [
        "--inputs",
        json.dumps(expected_inputs),
        "--outputs",
        json.dumps(expected_outputs),
    ]


def test_get_args_test_after_predict():
    pred = orc_mock.ModelFactory()
    data_manager = orc_mock.DataManagerFactory()
    ds1 = orc_mock.DataSampleFactory()
    ds2 = orc_mock.DataSampleFactory()
    task = orc_mock.ComputeTaskFactory(
        category=orchestrator.ComputeTaskCategory.TASK_TEST,
        rank=0,
    )
    algo = orc_mock.AlgoFactory(
        inputs={
            InputIdentifiers.PREDICTIONS: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_MODEL),
            InputIdentifiers.OPENER: orc_mock.AlgoInputFactory(kind=orchestrator.AssetKind.ASSET_DATA_MANAGER),
            InputIdentifiers.DATASAMPLES: orc_mock.AlgoInputFactory(
                kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, multiple=True
            ),
        }
    )

    input_assets = [
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.PREDICTIONS, kind=orchestrator.AssetKind.ASSET_MODEL, model=pred
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.OPENER,
            kind=orchestrator.AssetKind.ASSET_DATA_MANAGER,
            data_manager=data_manager,
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.DATASAMPLES, kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, data_sample=ds1
        ),
        ComputeTaskInputAsset(
            identifier=InputIdentifiers.DATASAMPLES, kind=orchestrator.AssetKind.ASSET_DATA_SAMPLE, data_sample=ds2
        ),
    ]

    ctx = context.Context(
        channel_name=_CHANNEL,
        task=task,
        input_assets=input_assets,
        algo=algo,
        has_chainkeys=False,
        compute_plan=None,
        directories=Directories(task.compute_plan_key),
    )
    ctx._outputs = [
        context.OutputResource(
            identifier=InputIdentifiers.PERFORMANCE,
            kind=orchestrator.AssetKind.ASSET_PERFORMANCE,
            multiple=False,
            rel_path=f"perf/{InputIdentifiers.PERFORMANCE}-perf.json",
        ),
    ]

    expected_inputs = [
        {"id": InputIdentifiers.PREDICTIONS, "value": f"/substra_internal/in_models/{pred.key}", "multiple": False},
        {
            "id": InputIdentifiers.OPENER,
            "value": f"/substra_internal/openers/{data_manager.key}/__init__.py",
            "multiple": False,
        },
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}", "multiple": True},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}", "multiple": True},
    ]

    expected_outputs = [
        {
            "id": InputIdentifiers.PERFORMANCE,
            "value": f"/substra_internal/perf/{InputIdentifiers.PERFORMANCE}-perf.json",
            "multiple": False,
        },
    ]

    actual = get_exec_command_args(ctx)
    assert actual == [
        "--rank",
        "0",
        "--inputs",
        json.dumps(expected_inputs),
        "--outputs",
        json.dumps(expected_outputs),
    ]

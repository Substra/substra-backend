import json

import orchestrator
import orchestrator.algo_pb2 as algo_pb2
import orchestrator.mock as orc_mock
from orchestrator.resources import ComputeTaskInputAsset
from substrapp.compute_tasks.command import _get_args
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import Directories
from substrapp.tests.common import InputIdentifiers
from substrapp.tests.orchestrator_factory import AlgoFactory

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

    ctx = Context(
        channel_name=_CHANNEL,
        task=task,
        compute_plan_tag="",
        input_assets=input_assets,
        algo=None,
        has_chainkeys=False,
        compute_plan={},
        directories=Directories(task.key),
    )

    expected_inputs = [
        {"id": InputIdentifiers.MODEL, "value": f"/substra_internal/in_models/{model.key}"},
        {"id": InputIdentifiers.OPENER, "value": f"/substra_internal/openers/{data_manager.key}/__init__.py"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}"},
    ]

    expected_outputs = [
        {"id": InputIdentifiers.MODEL, "value": "/substra_internal/out_models/out-model"},
    ]

    actual = _get_args(ctx)
    assert actual == [
        "train",
        "--rank",
        "0",
        "--inputs",
        f"'{json.dumps(expected_inputs)}'",
        "--outputs",
        f"'{json.dumps(expected_outputs)}'",
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

    ctx = Context(
        channel_name=_CHANNEL,
        task=task,
        compute_plan_tag="",
        input_assets=input_assets,
        algo=None,
        has_chainkeys=False,
        compute_plan={},
        directories=Directories(task.compute_plan_key),
    )

    expected_inputs = [
        {"id": InputIdentifiers.SHARED, "value": f"/substra_internal/in_models/{shared.key}"},
        {"id": InputIdentifiers.LOCAL, "value": f"/substra_internal/in_models/{local.key}"},
        {"id": InputIdentifiers.OPENER, "value": f"/substra_internal/openers/{data_manager.key}/__init__.py"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}"},
    ]

    expected_outputs = [
        {"id": InputIdentifiers.LOCAL, "value": "/substra_internal/out_models/out-head-model"},
        {"id": InputIdentifiers.SHARED, "value": "/substra_internal/out_models/out-model"},
    ]

    actual = _get_args(ctx)
    assert actual == [
        "train",
        "--rank",
        "0",
        "--inputs",
        f"'{json.dumps(expected_inputs)}'",
        "--outputs",
        f"'{json.dumps(expected_outputs)}'",
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

    ctx = Context(
        channel_name=_CHANNEL,
        task=task,
        compute_plan_tag="",
        input_assets=input_assets,
        algo=None,
        has_chainkeys=False,
        compute_plan={},
        directories=Directories(task.compute_plan_key),
    )

    expected_inputs = [
        {"id": InputIdentifiers.MODEL, "value": f"/substra_internal/in_models/{model.key}"},
        {"id": InputIdentifiers.OPENER, "value": f"/substra_internal/openers/{data_manager.key}/__init__.py"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}"},
    ]

    expected_outputs = [
        {"id": InputIdentifiers.PREDICTIONS, "value": "/substra_internal/out_models/out-model"},
    ]

    actual = _get_args(ctx)
    assert actual == [
        "predict",
        "--inputs",
        f"'{json.dumps(expected_inputs)}'",
        "--outputs",
        f"'{json.dumps(expected_outputs)}'",
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

    ctx = Context(
        channel_name=_CHANNEL,
        task=task,
        compute_plan_tag="",
        input_assets=input_assets,
        algo=None,
        has_chainkeys=False,
        compute_plan={},
        directories=Directories(task.compute_plan_key),
    )

    expected_inputs = [
        {"id": InputIdentifiers.LOCAL, "value": f"/substra_internal/in_models/{local.key}"},
        {"id": InputIdentifiers.SHARED, "value": f"/substra_internal/in_models/{shared.key}"},
        {"id": InputIdentifiers.OPENER, "value": f"/substra_internal/openers/{data_manager.key}/__init__.py"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}"},
    ]

    expected_outputs = [
        {"id": InputIdentifiers.PREDICTIONS, "value": "/substra_internal/out_models/out-model"},
    ]

    actual = _get_args(ctx)
    assert actual == [
        "predict",
        "--inputs",
        f"'{json.dumps(expected_inputs)}'",
        "--outputs",
        f"'{json.dumps(expected_outputs)}'",
    ]


def test_get_args_test_after_predict():
    algo = AlgoFactory(category=algo_pb2.AlgoCategory.ALGO_METRIC)
    pred = orc_mock.ModelFactory()
    data_manager = orc_mock.DataManagerFactory()
    ds1 = orc_mock.DataSampleFactory()
    ds2 = orc_mock.DataSampleFactory()
    task = orc_mock.ComputeTaskFactory(
        category=orchestrator.ComputeTaskCategory.TASK_TEST,
        rank=0,
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

    ctx = Context(
        channel_name=_CHANNEL,
        task=task,
        compute_plan_tag="",
        input_assets=input_assets,
        algo=algo,
        has_chainkeys=False,
        compute_plan={},
        directories=Directories(task.compute_plan_key),
    )

    cmd = [
        "--input-predictions-path",
        f"/substra_internal/in_models/{pred.key}",
        "--opener-path",
        f"/substra_internal/openers/{data_manager.key}/__init__.py",
        "--data-sample-paths",
    ]
    cmd.extend([f"/substra_internal/data_samples/{ds.key}" for ds in [ds1, ds2]])
    cmd.append("--output-perf-path")
    cmd.append(f"/substra_internal/perf/{ctx.algo.key}-perf.json")

    actual = _get_args(ctx)

    assert actual == cmd

import json

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.computetask_pb2 as computetask_pb2
from orchestrator.resources import ComputeTaskInputAsset
from substrapp.compute_tasks.command import _get_args
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import Directories
from substrapp.tests.common import InputIdentifiers
from substrapp.tests.orchestrator_factory import AlgoFactory
from substrapp.tests.orchestrator_factory import DataManagerFactory
from substrapp.tests.orchestrator_factory import DataSampleFactory
from substrapp.tests.orchestrator_factory import ModelFactory

_CHANNEL = "mychannel"


def test_get_args_train_task():
    model = ModelFactory()
    data_manager = DataManagerFactory()
    ds1 = DataSampleFactory()
    ds2 = DataSampleFactory()

    input_assets = [
        ComputeTaskInputAsset(computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.MODEL, model=model)),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.OPENER, data_manager=data_manager)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.DATASAMPLES, data_sample=ds1)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.DATASAMPLES, data_sample=ds2)
        ),
    ]

    ctx = Context(
        channel_name=_CHANNEL,
        task={
            "compute_plan_key": "cpkey",
            "rank": "0",
        },
        task_category=computetask_pb2.ComputeTaskCategory.TASK_TRAIN,
        compute_plan_tag="",
        input_assets=input_assets,
        algo=None,
        has_chainkeys=False,
        compute_plan={},
        compute_plan_key="cpkey",
        task_key="taskkey",
        directories=Directories("cpkey"),
    )

    expected_inputs = [
        {"id": InputIdentifiers.MODEL, "value": f"/substra_internal/in_models/{model.key}"},
        {"id": InputIdentifiers.OPENER, "value": f"/substra_internal/openers/{data_manager.key}/__init__.py"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}"},
    ]

    expected_outputs = [
        {"id": InputIdentifiers.MODEL, "value": "/substra_internal/out_models/out-model"},
        {"id": "localfolder", "value": "/substra_internal/local"},
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
    shared = ModelFactory()
    local = ModelFactory()
    data_manager = DataManagerFactory()
    ds1 = DataSampleFactory()
    ds2 = DataSampleFactory()

    input_assets = [
        ComputeTaskInputAsset(computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.SHARED, model=shared)),
        ComputeTaskInputAsset(computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.LOCAL, model=local)),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.OPENER, data_manager=data_manager)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.DATASAMPLES, data_sample=ds1)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.DATASAMPLES, data_sample=ds2)
        ),
    ]

    ctx = Context(
        channel_name=_CHANNEL,
        task={
            "compute_plan_key": "cpkey",
            "rank": "0",
        },
        task_category=computetask_pb2.ComputeTaskCategory.TASK_COMPOSITE,
        compute_plan_tag="",
        input_assets=input_assets,
        algo=None,
        has_chainkeys=False,
        compute_plan={},
        compute_plan_key="cpkey",
        task_key="taskkey",
        directories=Directories("cpkey"),
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
        {"id": "localfolder", "value": "/substra_internal/local"},
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
    model = ModelFactory()
    data_manager = DataManagerFactory()
    ds1 = DataSampleFactory()
    ds2 = DataSampleFactory()

    input_assets = [
        ComputeTaskInputAsset(computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.MODEL, model=model)),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.OPENER, data_manager=data_manager)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.DATASAMPLES, data_sample=ds1)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.DATASAMPLES, data_sample=ds2)
        ),
    ]

    ctx = Context(
        channel_name=_CHANNEL,
        task={
            "compute_plan_key": "cpkey",
            "rank": "0",
        },
        task_category=computetask_pb2.ComputeTaskCategory.TASK_PREDICT,
        compute_plan_tag="",
        input_assets=input_assets,
        algo=None,
        has_chainkeys=False,
        compute_plan={},
        compute_plan_key="cpkey",
        task_key="taskkey",
        directories=Directories("cpkey"),
    )

    expected_inputs = [
        {"id": InputIdentifiers.MODEL, "value": f"/substra_internal/in_models/{model.key}"},
        {"id": InputIdentifiers.OPENER, "value": f"/substra_internal/openers/{data_manager.key}/__init__.py"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds1.key}"},
        {"id": InputIdentifiers.DATASAMPLES, "value": f"/substra_internal/data_samples/{ds2.key}"},
    ]

    expected_outputs = [
        {"id": InputIdentifiers.PREDICTIONS, "value": "/substra_internal/out_models/out-model"},
        {"id": "localfolder", "value": "/substra_internal/local"},
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
    local = ModelFactory()
    shared = ModelFactory()
    data_manager = DataManagerFactory()
    ds1 = DataSampleFactory()
    ds2 = DataSampleFactory()

    input_assets = [
        ComputeTaskInputAsset(computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.LOCAL, model=local)),
        ComputeTaskInputAsset(computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.SHARED, model=shared)),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.OPENER, data_manager=data_manager)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.DATASAMPLES, data_sample=ds1)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.DATASAMPLES, data_sample=ds2)
        ),
    ]

    ctx = Context(
        channel_name=_CHANNEL,
        task={
            "compute_plan_key": "cpkey",
            "rank": "0",
        },
        task_category=computetask_pb2.ComputeTaskCategory.TASK_PREDICT,
        compute_plan_tag="",
        input_assets=input_assets,
        algo=None,
        has_chainkeys=False,
        compute_plan={},
        compute_plan_key="cpkey",
        task_key="taskkey",
        directories=Directories("cpkey"),
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
        {"id": "localfolder", "value": "/substra_internal/local"},
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
    pred = ModelFactory()
    data_manager = DataManagerFactory()
    ds1 = DataSampleFactory()
    ds2 = DataSampleFactory()

    input_assets = [
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.PREDICTIONS, model=pred)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.OPENER, data_manager=data_manager)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.DATASAMPLES, data_sample=ds1)
        ),
        ComputeTaskInputAsset(
            computetask_pb2.ComputeTaskInputAsset(identifier=InputIdentifiers.DATASAMPLES, data_sample=ds2)
        ),
    ]

    ctx = Context(
        channel_name=_CHANNEL,
        task={
            "compute_plan_key": "cpkey",
            "rank": "0",
        },
        task_category=computetask_pb2.ComputeTaskCategory.TASK_TEST,
        compute_plan_tag="",
        input_assets=input_assets,
        algo=algo,
        has_chainkeys=False,
        compute_plan={},
        compute_plan_key="cpkey",
        task_key="taskkey",
        directories=Directories("cpkey"),
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

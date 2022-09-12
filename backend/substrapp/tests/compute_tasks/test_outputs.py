import os
import tempfile

import pytest
from grpc import RpcError
from grpc import StatusCode
from pytest_mock import MockerFixture

import orchestrator
import orchestrator.model_pb2 as model_pb2
from orchestrator import mock
from substrapp.compute_tasks import context
from substrapp.compute_tasks.directories import Directories
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.outputs import OutputSaver
from substrapp.compute_tasks.outputs import _get_model_category


@pytest.mark.parametrize(
    ("has_chainkeys"),
    [True, False],
)
def test_commit_chainkeys(has_chainkeys: bool, mocker: MockerFixture):
    mock_commit_dir = mocker.patch("substrapp.compute_tasks.directories.commit_dir")

    ctx = context.Context(
        channel_name="channel",
        task=mock.ComputeTaskFactory(),
        compute_plan=None,
        input_assets=[],
        algo=mock.AlgoFactory(),
        directories=Directories("cpkey"),
        has_chainkeys=has_chainkeys,
    )
    saver = OutputSaver(ctx)

    saver.save_outputs()
    if has_chainkeys:
        mock_commit_dir.assert_called_once()
    else:
        mock_commit_dir.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("orc_raise"),
    [True, False],
)
def test_save_model(settings, mocker: MockerFixture, orc_raise: bool):
    from substrapp.models import Model

    settings.SUBTUPLE_DIR = tempfile.mkdtemp()

    ctx = context.Context(
        channel_name="channel",
        task=mock.ComputeTaskFactory(),
        compute_plan=None,
        input_assets=[],
        algo=mock.AlgoFactory(),
        directories=Directories("cpkey"),
        has_chainkeys=False,
    )
    output = context.OutputResource(
        identifier="model",
        kind=orchestrator.AssetKind.ASSET_MODEL,
        multiple=False,
        rel_path="out_models/out-model",
    )
    ctx._outputs = [output]

    model_src = os.path.join(ctx.directories.task_dir, output.rel_path)
    os.makedirs(os.path.join(ctx.directories.task_dir, TaskDirName.OutModels))
    with open(model_src, "w") as f:
        f.write("model content")

    saver = OutputSaver(ctx)

    client = mocker.MagicMock()
    client.__enter__.return_value = client
    if orc_raise:
        error = RpcError()
        error.details = "orchestrator unavailable"
        error.code = lambda: StatusCode.UNAVAILABLE
        client.register_models.side_effect = error

    add_model_from_path = mocker.patch("substrapp.compute_tasks.outputs.add_model_from_path")
    mocker.patch("substrapp.compute_tasks.outputs.get_orchestrator_client", return_value=client)

    try:
        saver.save_outputs()
    except RpcError as e:
        if not orc_raise:
            raise e  # unexpected exception

    client.register_models.assert_called_once()
    if not orc_raise:
        add_model_from_path.assert_called_once()
    else:
        add_model_from_path.assert_not_called()

    models = Model.objects.all()
    filtered_model_keys = [str(model.key) for model in models]
    assert len(filtered_model_keys) == (0 if orc_raise else 1)


@pytest.mark.parametrize(
    "identifier,expected_category",
    [
        ("local", model_pb2.MODEL_HEAD),
        ("head", model_pb2.MODEL_HEAD),
        ("shared", model_pb2.MODEL_SIMPLE),
        ("model", model_pb2.MODEL_SIMPLE),
        ("predictions", model_pb2.MODEL_SIMPLE),
        ("somethingelse", model_pb2.MODEL_SIMPLE),
    ],
)
def test_model_category_inference(identifier: str, expected_category: model_pb2.ModelCategory.ValueType):
    assert _get_model_category(identifier) == expected_category

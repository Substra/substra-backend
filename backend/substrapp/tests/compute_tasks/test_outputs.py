import os
import tempfile

import pytest
from pytest_mock import MockerFixture

import orchestrator
from orchestrator import mock
from substrapp.compute_tasks import context
from substrapp.compute_tasks.directories import Directories
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.outputs import OutputSaver


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
def test_save_model(settings, mocker: MockerFixture):
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
    add_model_from_path = mocker.patch("substrapp.compute_tasks.outputs.add_model_from_path")
    mocker.patch("substrapp.compute_tasks.outputs.get_orchestrator_client", return_value=client)

    saver.save_outputs()

    client.register_models.assert_called_once()
    add_model_from_path.assert_called_once()

    models = Model.objects.all()
    filtered_model_keys = [str(model.key) for model in models]
    assert len(filtered_model_keys) == 1

import os
import tempfile
from contextlib import nullcontext

import pytest
from pytest_mock import MockerFixture

import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import CPDirName
from substrapp.compute_tasks.directories import Directories
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.tasks.tasks_compute_task import compute_task
from substrapp.tests.orchestrator_factory import Orchestrator

CHANNEL = "mychannel"


@pytest.mark.parametrize("compute_job_raises", [False, True], ids=["wihtout_exception", "with_exception"])
def test_local_folder(compute_job_raises: bool, settings, mocker: MockerFixture, orchestrator: Orchestrator):
    """
    This test ensures that changes to the subtuple local folder are reflected to the compute plan local folder iff
    the tuple execution succeeds.
    """
    settings.LEDGER_CHANNELS = {CHANNEL: {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
    mocker.patch("substrapp.compute_tasks.context.get_orchestrator_client", return_value=orchestrator.client)
    mocker.patch("substrapp.tasks.tasks_compute_task.get_orchestrator_client", return_value=orchestrator.client)
    mocker.patch("substrapp.tasks.tasks_compute_task.init_asset_buffer")
    mocker.patch("substrapp.tasks.tasks_compute_task.init_compute_plan_dirs")
    mocker.patch("substrapp.tasks.tasks_compute_task.build_image_if_missing")
    mocker.patch("substrapp.tasks.tasks_compute_task.add_task_assets_to_buffer")
    mocker.patch("substrapp.tasks.tasks_compute_task.add_assets_to_taskdir")
    mock_execute_compute_task = mocker.patch("substrapp.tasks.tasks_compute_task.execute_compute_task")
    mocker.patch("substrapp.compute_tasks.outputs.save_models")
    mocker.patch("substrapp.tasks.tasks_compute_task.teardown_task_dirs")

    file = "model.txt"
    initial_value = "initial value"
    updated_value = "updated value"

    train_task = orchestrator.create_train_task(status=computetask_pb2.STATUS_DOING)
    train_task = orchestrator.client.query_task(train_task.key)

    # Setup a fake context
    ctx = Context(
        channel_name="mychannel",
        task=train_task,
        compute_plan_tag="",
        input_assets=[],
        algo=None,
        has_chainkeys=False,
        compute_plan={},
        directories=Directories("cpkey"),
    )

    class FakeDirectories:
        compute_plan_dir = tempfile.mkdtemp()
        task_dir = tempfile.mkdtemp()

    ctx._directories = FakeDirectories()
    ctx._has_chainkeys = False
    mock_ctx_from_task = mocker.patch("substrapp.tasks.tasks_compute_task.Context.from_task", return_value=ctx)

    local_folder = os.path.join(ctx.directories.task_dir, TaskDirName.Local)
    local_folder_committed = os.path.join(ctx.directories.compute_plan_dir, CPDirName.Local)

    # Write an initial value into the compute plan local folder
    os.makedirs(local_folder_committed, exist_ok=True)
    with open(os.path.join(local_folder_committed, file), "w") as x:
        x.write(initial_value)

    def execute(*args, **kwargs):
        del args, kwargs
        nonlocal local_folder
        with open(os.path.join(local_folder, file), "w") as x:
            x.write(updated_value)
            print("test")
        if compute_job_raises:
            raise Exception("I'm an error")

    mock_execute_compute_task.side_effect = execute

    # assert that it raises when it should
    context = pytest.raises(Exception) if compute_job_raises else nullcontext()
    with context as excinfo:
        compute_task(CHANNEL, train_task.json(), train_task.compute_plan_key)

    # Check the compute plan local folder value is correct:
    # - If do_task did raise an exception then the local value should be unchanged
    # - If do_task did not raise an exception then the local value should be updated
    with open(os.path.join(local_folder_committed, file), "r") as x:
        content = x.read()
    expected = initial_value if compute_job_raises else updated_value
    assert content == expected

    mock_execute_compute_task.assert_called_once()
    mock_ctx_from_task.assert_called_once()

    # check that it was the expected exception that was raised
    if compute_job_raises:
        assert "I'm an error" in str(excinfo.value.__cause__)

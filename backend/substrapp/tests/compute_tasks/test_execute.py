import uuid

import pytest
from pytest_mock import MockerFixture

from substrapp.compute_tasks import compute_pod
from substrapp.compute_tasks import execute
from substrapp.compute_tasks.errors import ExecutionError


def test_exec_success(mocker: MockerFixture):
    execution_stream = mocker.Mock()
    execution_stream.is_open.return_value = False
    execution_stream.returncode = 0
    mock_get_exec_stream = mocker.patch("substrapp.compute_tasks.execute.execute")
    mock_get_exec_stream.return_value = execution_stream

    ctx = mocker.Mock()
    ctx.directories = mocker.Mock()
    pod = compute_pod.ComputePod(str(uuid.uuid4()), str(uuid.uuid4()))

    mocker.patch("substrapp.compute_tasks.execute.get_exec_command", return_value=["ls", "/tmp"])
    mocker.patch("substrapp.compute_tasks.execute.get_exec_command_args")
    mocker.patch("substrapp.compute_tasks.execute.write_command_args_file")

    execute._exec(ctx, pod)

    mock_get_exec_stream.assert_called_once()


def test_exec_failure(mocker: MockerFixture):
    retcode = 123
    execution_stream = mocker.Mock()
    execution_stream.is_open.return_value = False
    execution_stream.returncode = 123
    mock_get_exec_stream = mocker.patch("substrapp.compute_tasks.execute.execute")
    mock_get_exec_stream.return_value = execution_stream

    ctx = mocker.Mock()
    ctx.directories = mocker.Mock()
    pod = compute_pod.ComputePod(str(uuid.uuid4()), str(uuid.uuid4()))

    mocker.patch("substrapp.compute_tasks.execute.get_exec_command", return_value=["ls", "/tmp"])
    mocker.patch("substrapp.compute_tasks.execute.get_exec_command_args")
    mocker.patch("substrapp.compute_tasks.execute.write_command_args_file")

    with pytest.raises(ExecutionError) as exc:
        execute._exec(ctx, pod)

    assert str(retcode) in str(exc.value)
    mock_get_exec_stream.assert_called_once()

import datetime
import errno
import io
import tempfile
from functools import wraps
from typing import Type
from unittest.mock import MagicMock

import pytest
from grpc import RpcError
from grpc import StatusCode
from pytest_mock import MockerFixture
from rest_framework import status

import orchestrator
import orchestrator.mock as orc_mock
from substrapp.compute_tasks import errors
from substrapp.compute_tasks.context import Context
from substrapp.exceptions import OrganizationHttpError
from substrapp.models import FailedAssetKind
from substrapp.tasks import tasks_compute_task
from substrapp.tasks.tasks_compute_task import compute_task
from substrapp.utils.errors import store_failure

CHANNEL = "mychannel"


def test_compute_task_exception(mocker: MockerFixture):
    mocker.patch("substrapp.tasks.tasks_compute_task.get_orchestrator_client")
    mock_raise_if_not_runnable = mocker.patch("substrapp.compute_tasks.compute_task._raise_if_task_not_runnable")
    mock_start_task = mocker.patch("substrapp.compute_tasks.compute_task.start_task_if_not_started")
    mock_init_cp_dirs = mocker.patch("substrapp.tasks.tasks_compute_task.init_compute_plan_dirs")
    mock_init_task_dirs = mocker.patch("substrapp.tasks.tasks_compute_task.init_task_dirs")
    mock_add_asset_to_buffer = mocker.patch("substrapp.tasks.tasks_compute_task.add_task_assets_to_buffer")
    mock_add_asset_to_task_dir = mocker.patch("substrapp.tasks.tasks_compute_task.add_assets_to_taskdir")
    mock_load_remote_function_image = mocker.patch("substrapp.compute_tasks.image_builder.load_remote_function_image")
    mock_wait_for_image_built = mocker.patch("substrapp.compute_tasks.image_builder.wait_for_image_built")
    mock_execute_compute_task = mocker.patch("substrapp.tasks.tasks_compute_task.execute_compute_task")
    saver = mocker.MagicMock()
    mock_output_saver = mocker.patch("substrapp.tasks.tasks_compute_task.OutputSaver", return_value=saver)
    mock_teardown_task_dirs = mocker.patch("substrapp.tasks.tasks_compute_task.teardown_task_dirs")

    class FakeDirectories:
        compute_plan_dir = tempfile.mkdtemp()
        task_dir = tempfile.mkdtemp()

    task = orc_mock.ComputeTaskFactory(
        status=orchestrator.ComputeTaskStatus.STATUS_DOING,
    )
    # Setup a fake context
    ctx = Context(
        channel_name=CHANNEL,
        task=task,
        compute_plan=None,
        input_assets=[],
        function=orc_mock.FunctionFactory(),
        directories=FakeDirectories(),
        has_chainkeys=False,
    )

    mock_ctx_from_task = mocker.patch("substrapp.tasks.tasks_compute_task.Context.from_task", return_value=ctx)

    compute_task(CHANNEL, task.json(), None)

    assert mock_raise_if_not_runnable.call_count == 2
    mock_ctx_from_task.assert_called_once()
    mock_start_task.assert_called_once()
    mock_init_cp_dirs.assert_called_once()
    mock_init_task_dirs.assert_called_once()
    mock_add_asset_to_buffer.assert_called_once()
    mock_add_asset_to_task_dir.assert_called_once()
    mock_load_remote_function_image.assert_called_once()
    mock_wait_for_image_built.assert_called_once()
    mock_execute_compute_task.assert_called_once()
    saver.save_outputs.assert_called_once()
    mock_output_saver.assert_called_once()
    mock_teardown_task_dirs.assert_called_once()

    # test RPC error
    error = RpcError()
    error.details = "OE0000"
    error.code = lambda: StatusCode.NOT_FOUND

    saver.save_outputs.side_effect = error
    with pytest.raises(errors.CeleryRetryError) as excinfo:
        compute_task(CHANNEL, task.json(), None)
    assert str(excinfo.value.__cause__.details) == "OE0000"

    # test compute error
    mock_execute_compute_task.side_effect = Exception("Test")
    with pytest.raises(errors.CeleryRetryError) as excinfo:
        compute_task(CHANNEL, task.json(), None)

    assert str(excinfo.value.__cause__) == "Test"

    # test not enough space on disk error
    mock_execute_compute_task.side_effect = OSError(errno.ENOSPC, "No space left on device")
    with pytest.raises(errors.CeleryRetryError) as excinfo:
        compute_task(CHANNEL, task.json(), None)
    assert "No space left on device" in str(excinfo.value.__cause__)

    # test other OS error
    mock_execute_compute_task.side_effect = OSError(errno.EACCES, "Dummy error")
    with pytest.raises(errors.CeleryRetryError) as excinfo:
        compute_task(CHANNEL, task.json(), None)
    assert "Dummy error" in str(excinfo.value.__cause__)


@pytest.fixture
def mock_retry(mocker: MockerFixture) -> MagicMock:
    def basic_retry(exc, **retry_kwargs):
        # retry function that just re-raise the exception
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                return f(*args, **kwargs)

            return decorated_function

        return decorator
        # return exc

    mock_retry = mocker.patch("substrapp.tasks.tasks_compute_task.ComputeTask.retry")
    # Explicitly set a side_effect for mock_retry that return an Exception,
    # otherwise mock_retry will be a MagicMock, which will make celery unhappy
    mock_retry.side_effect = basic_retry

    return mock_retry


def test_celery_retry(mocker: MockerFixture):
    mocker.patch("substrapp.tasks.tasks_compute_task.get_orchestrator_client")
    mocker.patch("substrapp.compute_tasks.compute_task._raise_if_task_not_runnable")
    mocker.patch("substrapp.compute_tasks.compute_task.start_task_if_not_started")
    mocker.patch("substrapp.tasks.tasks_compute_task.Context.from_task")
    mocker.patch("substrapp.tasks.tasks_compute_task.init_compute_plan_dirs")
    mocker.patch("substrapp.tasks.tasks_compute_task.init_task_dirs")
    mocker.patch("substrapp.tasks.tasks_compute_task._prepare_chainkeys")
    mocker.patch("substrapp.tasks.tasks_compute_task.add_task_assets_to_buffer")
    mocker.patch("substrapp.tasks.tasks_compute_task.add_assets_to_taskdir")
    mocker.patch("substrapp.tasks.tasks_compute_task.restore_dir")
    mocker.patch("substrapp.compute_tasks.image_builder.load_remote_function_image")
    mocker.patch("substrapp.compute_tasks.image_builder.wait_for_image_built")
    mock_execute_compute_task = mocker.patch("substrapp.tasks.tasks_compute_task.execute_compute_task")
    mocker.patch("substrapp.tasks.tasks_compute_task.teardown_task_dirs")
    mock_retry = mocker.patch("substrapp.tasks.tasks_compute_task.ComputeTask.retry")
    mock_clear_asset_buffer = mocker.patch("substrapp.tasks.tasks_compute_task.clear_assets_buffer")

    task = orc_mock.ComputeTaskFactory()

    def basic_retry(exc, **retry_kwargs):
        # retry function that just re-raise the exception
        return exc

    # Explicitly set a side_effect for mretry that return an Exception,
    # otherwise mretry will be a MagicMock, which will make celery unhappy
    mock_retry.side_effect = basic_retry

    # retry because of generic exception
    exception_message = "an exception that should trigger the retry mechanism"
    mock_execute_compute_task.side_effect = Exception(exception_message)

    with pytest.raises(errors.CeleryRetryError) as excinfo:
        compute_task(CHANNEL, task.json(), None)

    assert str(excinfo.value.__cause__) == exception_message
    mock_retry.assert_called_once()

    # retry because no space left on device error
    mock_execute_compute_task.side_effect = IOError(errno.ENOSPC, "no file left on device")

    with pytest.raises(errors.CeleryRetryError) as excinfo:
        compute_task(CHANNEL, task.json(), None)

    assert "no file left on device" in str(excinfo.value.__cause__)
    assert mock_retry.call_count == 2
    mock_clear_asset_buffer.assert_called_once()

    # do not retry because the error happened in the compute pod
    mock_execute_compute_task.side_effect = errors.ExecutionError("python not found", "Error while running command")

    with pytest.raises(errors.CeleryNoRetryError) as excinfo:
        compute_task(CHANNEL, task.json(), None)

    assert "Error while running command" in str(excinfo.value)
    assert mock_retry.call_count == 2


@pytest.mark.django_db
@pytest.mark.parametrize("logs", [b"", b"Hello, World!"])
def test_store_failure_execution_error(logs: bytes):
    compute_task_key = "42ff54eb-f4de-43b2-a1a0-a9f4c5f4737f"
    exc = errors.ExecutionError(logs=io.BytesIO(logs))

    failure_report = store_failure(exc, compute_task_key, FailedAssetKind.FAILED_ASSET_COMPUTE_TASK)
    failure_report.refresh_from_db()

    assert str(failure_report.asset_key) == compute_task_key
    assert failure_report.logs.read() == logs


@pytest.mark.parametrize("exc_class", [Exception])
def test_store_failure_ignored_exception(exc_class: Type[Exception]):
    assert store_failure(exc_class(), "uuid", FailedAssetKind.FAILED_ASSET_COMPUTE_TASK) is None


@pytest.mark.django_db
def test_send_profiling_event(mock_retry: MagicMock, mocker: MockerFixture):
    mock_post = mocker.patch("substrapp.clients.organization.post")
    mock_put = mocker.patch("substrapp.clients.organization.put")
    params = {"channel_name": CHANNEL, "url_create": "testurl", "url_update": "testurl", "data": {}}
    tasks_compute_task._send_profiling_event(**params)
    mock_post.side_effect = OrganizationHttpError(url="testurl", status_code=status.HTTP_409_CONFLICT)
    tasks_compute_task._send_profiling_event(**params)

    assert mock_post.call_count == 2
    assert mock_put.call_count == 1


@pytest.mark.django_db
def test_create_task_profiling_update(mock_retry: MagicMock, mocker: MockerFixture):
    mock_post = mocker.patch("substrapp.clients.organization.post")
    mock_put = mocker.patch("substrapp.clients.organization.put")
    compute_task_key = "42ff54eb-f4de-43b2-a1a0-a9f4c5f4737f"
    tasks_compute_task._create_task_profiling(CHANNEL, compute_task_key)
    mock_post.side_effect = OrganizationHttpError(url="testurl", status_code=status.HTTP_409_CONFLICT)
    tasks_compute_task._create_task_profiling(CHANNEL, compute_task_key)

    assert mock_post.call_count == 2
    assert mock_put.call_count == 1


@pytest.mark.django_db
def test_create_task_profiling_step_update(mock_retry: MagicMock, mocker: MockerFixture):
    mock_post = mocker.patch("substrapp.clients.organization.post")
    mock_put = mocker.patch("substrapp.clients.organization.put")
    params = {
        "channel_name": CHANNEL,
        "compute_task_key": "42ff54eb-f4de-43b2-a1a0-a9f4c5f4737f",
        "field": tasks_compute_task.ComputeTaskSteps.BUILD_IMAGE,
        "duration": datetime.timedelta(seconds=20),
    }

    tasks_compute_task._create_task_profiling_step(**params)
    mock_post.side_effect = OrganizationHttpError(url="testurl", status_code=status.HTTP_409_CONFLICT)
    tasks_compute_task._create_task_profiling_step(**params)

    assert mock_post.call_count == 2
    assert mock_put.call_count == 1

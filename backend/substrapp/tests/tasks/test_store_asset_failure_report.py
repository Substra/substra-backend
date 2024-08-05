import io
import pickle
from typing import Type

import pytest
from pytest_mock import MockerFixture

from builder import exceptions as build_errors
from orchestrator import failure_report_pb2
from substrapp.compute_tasks import errors
from substrapp.compute_tasks.errors import ComputeTaskErrorType
from substrapp.models import FailedAssetKind
from substrapp.tasks.tasks_asset_failure_report import get_error_type
from substrapp.tasks.tasks_asset_failure_report import store_asset_failure_report
from substrapp.utils.errors import store_failure

CHANNEL = "mychannel"


@pytest.fixture
def mock_orchestrator_client(mocker: MockerFixture):
    return mocker.patch("substrapp.tasks.tasks_asset_failure_report.get_orchestrator_client")


@pytest.mark.django_db
def test_store_asset_failure_report_success(mock_orchestrator_client: MockerFixture):
    exc = errors.ExecutionError(io.BytesIO(b"logs"))
    exception_pickled = pickle.dumps(exc)
    store_asset_failure_report(
        asset_key="e21f6352-75c1-4b79-9a00-1f547697ef25",
        asset_type=FailedAssetKind.FAILED_ASSET_COMPUTE_TASK,
        channel_name=CHANNEL,
        exception_pickled=exception_pickled,
    )


def test_store_asset_failure_report_ignored(mock_orchestrator_client):
    exception_pickled = pickle.dumps(Exception())
    store_asset_failure_report(
        asset_key="750836e4-0def-465a-8397-57c49ebd38bf",
        asset_type=FailedAssetKind.FAILED_ASSET_COMPUTE_TASK,
        channel_name=CHANNEL,
        exception_pickled=exception_pickled,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("logs", [b"", b"Hello, World!"])
def test_store_failure_execution_error(logs: bytes):
    compute_task_key = "42ff54eb-f4de-43b2-a1a0-a9f4c5f4737f"
    exc = errors.ExecutionError(logs=io.BytesIO(logs))

    failure_report = store_failure(
        exc,
        compute_task_key,
        FailedAssetKind.FAILED_ASSET_COMPUTE_TASK,
        error_type=ComputeTaskErrorType.EXECUTION_ERROR.value,
    )
    failure_report.refresh_from_db()

    assert str(failure_report.asset_key) == compute_task_key
    assert failure_report.logs.read() == logs


@pytest.mark.parametrize("exc_class", [Exception])
def test_store_failure_ignored_exception(exc_class: Type[Exception]):
    assert (
        store_failure(
            exc_class(), "uuid", FailedAssetKind.FAILED_ASSET_COMPUTE_TASK, ComputeTaskErrorType.INTERNAL_ERROR.value
        )
        is None
    )


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (build_errors.BuildError(logs="some build error"), failure_report_pb2.ERROR_TYPE_BUILD),
        (errors.ExecutionError(logs=io.BytesIO()), failure_report_pb2.ERROR_TYPE_EXECUTION),
        (Exception(), failure_report_pb2.ERROR_TYPE_INTERNAL),
    ],
)
def test_get_error_type(exc: Exception, expected: str):
    assert get_error_type(exc) == expected

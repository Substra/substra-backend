import datetime
import uuid
from typing import Optional
from typing import Type
from unittest import mock

import pytest

import orchestrator
import orchestrator.client as orc_client
import orchestrator.mock as orc_mock
from substrapp.compute_tasks import compute_task as task_utils

RUNNABLE_TASK_STATUSES = task_utils._RUNNABLE_TASK_STATUSES
NON_RUNNABLE_TASK_STATUSES = [
    orchestrator.ComputeTaskStatus.STATUS_WAITING_FOR_PARENT_TASKS,
    orchestrator.ComputeTaskStatus.STATUS_DONE,
    orchestrator.ComputeTaskStatus.STATUS_FAILED,
    orchestrator.ComputeTaskStatus.STATUS_CANCELED,
]


@pytest.mark.parametrize(
    ("task_status", "is_runnable"),
    [(s, True) for s in RUNNABLE_TASK_STATUSES] + [(s, False) for s in NON_RUNNABLE_TASK_STATUSES],
)
def test_is_task_status_runnable(task_status: orchestrator.ComputeTaskStatus, is_runnable: bool):
    compute_task = orc_mock.ComputeTaskFactory(status=task_status)
    assert task_utils._is_task_status_runnable(compute_task, allow_doing=False) is is_runnable


def test_is_task_status_runnable_allow_doing():
    compute_task = orc_mock.ComputeTaskFactory(status=orchestrator.ComputeTaskStatus.STATUS_DOING)
    assert task_utils._is_task_status_runnable(compute_task, allow_doing=True)


@pytest.fixture
def client() -> mock.Mock:
    return mock.Mock(spec=orc_client.OrchestratorClient)


@pytest.mark.parametrize("task_status", NON_RUNNABLE_TASK_STATUSES)
def test_raise_if_task_not_runnable_raise_TaskNonRunnableStatusError(task_status: str, client: mock.Mock):  # noqa: N802
    task = orc_mock.ComputeTaskFactory(status=task_status)

    with pytest.raises(task_utils.TaskNonRunnableStatusError) as exc:
        task_utils._raise_if_task_not_runnable(str(uuid.uuid4()), client, existing_task=task)
        assert exc.status == task_status


@pytest.mark.parametrize(
    ("compute_plan_cancelation_date", "compute_plan_failure_date"),
    [
        (datetime.datetime.now(), None),
        (None, datetime.datetime.now()),
    ],
)
def test_raise_if_task_not_runnable_raise_ComputePlanNonRunnableError(  # noqa: N802
    compute_plan_cancelation_date: Optional[datetime.datetime],
    compute_plan_failure_date: Optional[datetime.datetime],
    client: mock.Mock,
):
    task_status = RUNNABLE_TASK_STATUSES[0]
    task = orc_mock.ComputeTaskFactory(status=task_status, compute_plan_key="cp-key")
    client.query_compute_plan.return_value = orc_mock.ComputePlanFactory(
        cancelation_date=compute_plan_cancelation_date,
        failure_date=compute_plan_failure_date,
    )

    with pytest.raises(task_utils.ComputePlanNonRunnableError) as exc:
        task_utils._raise_if_task_not_runnable(str(uuid.uuid4()), client, existing_task=task)
        assert exc.cancelation_date == compute_plan_cancelation_date
        assert exc.failure_date == compute_plan_failure_date

    client.query_compute_plan.assert_called_once()


@pytest.mark.parametrize("task_status", RUNNABLE_TASK_STATUSES)
def test_raise_if_task_not_runnable_do_not_raise(task_status: str, client: mock.Mock):
    task = orc_mock.ComputeTaskFactory(status=task_status, compute_plan_key="cp-key")
    client.query_compute_plan.return_value = orc_mock.ComputePlanFactory()

    task_utils._raise_if_task_not_runnable(str(uuid.uuid4()), client, existing_task=task)

    client.query_compute_plan.assert_called_once()


def test_raise_if_task_not_runnable_allow_doing_do_not_raise(client: mock.Mock):
    task = orc_mock.ComputeTaskFactory(status=orchestrator.ComputeTaskStatus.STATUS_DOING, compute_plan_key="cp-key")
    client.query_compute_plan.return_value = orc_mock.ComputePlanFactory()

    task_utils._raise_if_task_not_runnable(str(uuid.uuid4()), client, allow_doing=True, existing_task=task)

    client.query_compute_plan.assert_called_once()


@pytest.mark.parametrize(
    "exception", [task_utils.TaskNonRunnableStatusError, task_utils.ComputePlanNonRunnableError, None]
)
@mock.patch("substrapp.compute_tasks.compute_task.raise_if_task_not_runnable", autospec=True)
def is_task_runnable(_raise_if_task_not_runnable: mock.Mock, exception: Optional[Type[Exception]]):
    _raise_if_task_not_runnable.side_effect = [exception]
    expected = not exception
    assert task_utils.is_task_runnable("task-key", None) is expected


@pytest.mark.parametrize(
    "status, should_update",
    [
        (orchestrator.ComputeTaskStatus.STATUS_TODO, True),
        (orchestrator.ComputeTaskStatus.STATUS_DOING, False),
    ],
)
def test_start_task_if_not_started(client: mock.Mock, status, should_update: bool):
    task = orc_mock.ComputeTaskFactory(status=status)

    task_utils.start_task_if_not_started(task, client)

    if should_update:
        client.update_task_status.assert_called_once()

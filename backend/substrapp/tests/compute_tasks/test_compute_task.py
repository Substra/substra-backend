import itertools
import uuid
from typing import Optional
from typing import Type
from unittest import mock

import pytest

import orchestrator.computetask_pb2 as computetask_pb2
from orchestrator import client as orc_client
from substrapp.compute_tasks import compute_task as task_utils

RUNNABLE_TASK_STATUSES = sorted(task_utils._RUNNABLE_TASK_STATUSES)
NON_RUNNABLE_TASK_STATUSES = sorted(task_utils._NON_RUNNABLE_TASK_STATUSES)


@pytest.mark.parametrize(
    ("task_status", "is_runnable"),
    [(s, True) for s in RUNNABLE_TASK_STATUSES] + [(s, False) for s in NON_RUNNABLE_TASK_STATUSES],
)
def test_is_task_status_runnable(task_status: str, is_runnable: bool):
    compute_task = {"status": task_status}
    assert task_utils._is_task_status_runnable(compute_task, allow_doing=False) is is_runnable


def test_is_task_status_runnable_allow_doing():
    compute_task = {"status": task_utils._TASK_STATUS_DOING}
    assert task_utils._is_task_status_runnable(compute_task, allow_doing=True)


RUNNABLE_COMPUTE_PLAN_STATUSES = sorted(task_utils._RUNNABLE_COMPUTE_PLAN_STATUSES)
NON_RUNNABLE_COMPUTE_PLAN_STATUSES = sorted(task_utils._NON_RUNNABLE_COMPUTE_PLAN_STATUSES)


@pytest.mark.parametrize(
    ("compute_plan_status", "is_runnable"),
    [(s, True) for s in RUNNABLE_COMPUTE_PLAN_STATUSES] + [(s, False) for s in NON_RUNNABLE_COMPUTE_PLAN_STATUSES],
)
def test_is_compute_plan_status_runnable(compute_plan_status: int, is_runnable: bool):
    compute_plan = {"status": compute_plan_status}
    assert task_utils._is_compute_plan_status_runnable(compute_plan) is is_runnable


@pytest.fixture
def client() -> mock.Mock:
    return mock.Mock(spec=orc_client.OrchestratorClient)


@pytest.mark.parametrize("task_status", NON_RUNNABLE_TASK_STATUSES)
def test_raise_if_task_not_runnable_raise_TaskNonRunnableStatusError(task_status: str, client: mock.Mock):  # noqa: N802
    task = {"status": task_status}

    with pytest.raises(task_utils.TaskNonRunnableStatusError) as exc:
        task_utils._raise_if_task_not_runnable(str(uuid.uuid4()), client, task=task)
        assert exc.status == task_status


@pytest.mark.parametrize("compute_plan_status", NON_RUNNABLE_COMPUTE_PLAN_STATUSES)
def test_raise_if_task_not_runnable_raise_ComputePlanNonRunnableStatusError(  # noqa: N802
    compute_plan_status: str, client: mock.Mock
):
    task_status = RUNNABLE_TASK_STATUSES[0]
    task = {"status": task_status, "compute_plan_key": "cp-key"}
    client.query_compute_plan.return_value = {"status": compute_plan_status}

    with pytest.raises(task_utils.ComputePlanNonRunnableStatusError) as exc:
        task_utils._raise_if_task_not_runnable(str(uuid.uuid4()), client, task=task)
        assert exc.status == compute_plan_status

    client.query_compute_plan.assert_called_once()


@pytest.mark.parametrize(
    ("task_status", "compute_plan_status"),
    list(itertools.product(RUNNABLE_TASK_STATUSES, RUNNABLE_COMPUTE_PLAN_STATUSES)),
)
def test_raise_if_task_not_runnable_do_not_raise(task_status: str, compute_plan_status: str, client: mock.Mock):
    task = {"status": task_status, "compute_plan_key": "cp-key"}
    client.query_compute_plan.return_value = {"status": compute_plan_status}

    task_utils._raise_if_task_not_runnable(str(uuid.uuid4()), client, task=task)

    client.query_compute_plan.assert_called_once()


@pytest.mark.parametrize("compute_plan_status", RUNNABLE_COMPUTE_PLAN_STATUSES)
def test_raise_if_task_not_runnable_allow_doing_do_not_raise(compute_plan_status: str, client: mock.Mock):
    task = {"status": task_utils._TASK_STATUS_DOING, "compute_plan_key": "cp-key"}
    client.query_compute_plan.return_value = {"status": compute_plan_status}

    task_utils._raise_if_task_not_runnable(str(uuid.uuid4()), client, allow_doing=True, task=task)

    client.query_compute_plan.assert_called_once()


@pytest.mark.parametrize(
    "exception", [task_utils.TaskNonRunnableStatusError, task_utils.ComputePlanNonRunnableStatusError, None]
)
@mock.patch("substrapp.compute_tasks.compute_task.raise_if_task_not_runnable", autospec=True)
def is_task_runnable(_raise_if_task_not_runnable: mock.Mock, exception: Optional[Type[Exception]]):
    _raise_if_task_not_runnable.side_effect = [exception]
    expected = not exception
    assert task_utils.is_task_runnable("task-key", None) is expected


@pytest.mark.parametrize(
    "status, should_update",
    [
        (computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_TODO), True),
        (computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_DOING), False),
    ],
)
def test_start_task_if_not_started(client: mock.Mock, status, should_update: bool):
    task = {"status": status, "key": uuid.uuid4()}

    task_utils.start_task_if_not_started(task, client)

    if should_update:
        client.update_task_status.assert_called_once()

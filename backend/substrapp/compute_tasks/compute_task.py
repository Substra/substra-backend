import datetime
from typing import Optional

import structlog

import orchestrator
from orchestrator import computetask_pb2
from orchestrator.error import OrcError
from orchestrator.resources import ComputeTask
from orchestrator.resources import ComputeTaskStatus

_RUNNABLE_TASK_STATUSES = [ComputeTaskStatus.STATUS_WAITING_FOR_EXECUTOR_SLOT]

logger = structlog.get_logger(__name__)


def _is_task_status_runnable(task: ComputeTask, allow_executing: bool) -> bool:
    if allow_executing:
        return task.status in _RUNNABLE_TASK_STATUSES + [ComputeTaskStatus.STATUS_EXECUTING]

    return task.status in _RUNNABLE_TASK_STATUSES


class TaskNonRunnableStatusError(RuntimeError):
    """The compute task status prevents running the task.

    Attributes:
        status: the status of the compute task.

    """

    def __init__(self, status: str) -> None:
        self.status = status


class ComputePlanNonRunnableError(RuntimeError):
    """The compute plan state prevents running the task."""

    def __init__(
        self, cancelation_date: Optional[datetime.datetime], failure_date: Optional[datetime.datetime]
    ) -> None:
        self.cancelation_date = cancelation_date
        self.failure_date = failure_date


def _raise_if_task_not_runnable(
    task_key: str,
    client: orchestrator.Client,
    allow_executing: bool = False,
    existing_task: ComputeTask = None,
) -> None:
    """Raise an exception if a compute task is not runnable by taking into account its status
    and the status of the associated compute plan.

    Args:
        task_key: the compute task key
        client: the orchestrator gRPC client.
        allow_executing: whether a compute task with the status DOING should be considered as runnable.
        existing_task: the compute task.
            if specified this task will be used to check the status instead of retrieving a task

    Returns:
        None if the task is runnable.

    Raises:
        TaskNonRunnableStatusError: if the compute task is not runnable because of its status.
        ComputePlanNonRunnableStatusError: if the compute task is not runnable because the status
            of its associated compute plan.

    """
    task: ComputeTask = existing_task if existing_task else client.query_task(task_key)

    if not _is_task_status_runnable(task, allow_executing):
        raise TaskNonRunnableStatusError(task.status.name)

    compute_plan = client.query_compute_plan(task.compute_plan_key)
    if not compute_plan.is_runnable:
        raise ComputePlanNonRunnableError(compute_plan.cancelation_date, compute_plan.failure_date)


def is_task_runnable(task_key: str, client: orchestrator.Client, allow_executing: bool = False) -> bool:
    """Check whether a compute task is runnable given its status and the status of the associated compute plan.

    Args:
        task_key: the key of the compute task.
        client: the orchestrator gRPC client.
        allow_executing: whether a compute task with the status EXECUTING should be considered as runnable.

    Returns:
        True if the compute task is runnable, False otherwise.

    """
    try:
        _raise_if_task_not_runnable(task_key, client, allow_executing)
    except (TaskNonRunnableStatusError, ComputePlanNonRunnableError):
        return False
    else:
        return True


def abort_task_if_not_runnable(
    task_key: str, client: orchestrator.Client, allow_executing: bool = False, task: ComputeTask = None
) -> None:
    """Cancel a compute task if its associated compute plan is not runnable. In addition, raise an error if the compute
    task is not runnable because of its status or the status of its compute plan.

    Args:
        task_key: the compute task key.
        client: the orchestrator gRPC client.
        allow_executing: whether a compute task with the status DOING should be considered as runnable.
        task: the compute task. if specified this task will be used to check the status instead of retrieving a task.

    Returns:
        None if the task is runnable.

    Raises:
        TaskNonRunnableStatusError: if the compute task is not runnable because of its status.
        ComputePlanNonRunnableStatusError: if the compute task is not runnable because the status
            of its associated compute plan.

    """
    try:
        _raise_if_task_not_runnable(task_key, client, allow_executing=allow_executing, existing_task=task)
    except ComputePlanNonRunnableError as exc:
        logger.info(
            "Compute plan not runnable. Canceling task.",
            compute_plan_cancelation_date=exc.cancelation_date,
            compute_plan_failure_date=exc.failure_date,
        )
        client.update_task_status(
            task_key,
            computetask_pb2.TASK_ACTION_CANCELED,
            log="Compute plan is not runnable",
        )
        raise


def start_task_if_not_started(task: ComputeTask, client: orchestrator.Client) -> None:
    """Start a compute task if it is not already started

    Args:
        task: the compute task.
        client: the orchestrator gRPC client.

    Returns:
        None

    Raises:
        OrcError: if the status can't be updated to DOING
    """
    if task.status == ComputeTaskStatus.STATUS_WAITING_FOR_EXECUTOR_SLOT:
        try:
            logger.info("Updating task status to STATUS_EXECUTING", task_key=task.key)
            client.update_task_status(task.key, computetask_pb2.TASK_ACTION_EXECUTING)
        except OrcError as rpc_error:
            logger.exception(
                f"failed to update task status to DOING, {rpc_error.details}",
                task_key=task.key,
            )
            raise


def mark_as_done(task_key: str, client: orchestrator.Client) -> None:
    """Transition a compute task to DONE

    Args:
        task_key: the key of the compute task to set to DONE.
        client: the orchestrator gRPC client.
    """
    try:
        client.update_task_status(task_key, computetask_pb2.TASK_ACTION_DONE, "task completed")
    except OrcError as err:
        if "transitionDone inappropriate in current state STATUS_DONE" in err.details:
            return
        raise

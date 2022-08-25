import structlog

import orchestrator
import orchestrator.client as orc_client
import orchestrator.computetask_pb2 as computetask_pb2
from orchestrator.error import OrcError
from orchestrator.resources import ComputeTask
from orchestrator.resources import ComputeTaskStatus

_RUNNABLE_TASK_STATUSES = [ComputeTaskStatus.STATUS_TODO]

_RUNNABLE_COMPUTE_PLAN_STATUSES = [
    orchestrator.ComputePlanStatus.PLAN_STATUS_TODO,
    orchestrator.ComputePlanStatus.PLAN_STATUS_DOING,
]

logger = structlog.get_logger(__name__)


def _is_task_status_runnable(task: ComputeTask, allow_doing: bool) -> bool:
    if allow_doing:
        return task.status in _RUNNABLE_TASK_STATUSES + [ComputeTaskStatus.STATUS_DOING]

    return task.status in _RUNNABLE_TASK_STATUSES


def _is_compute_plan_status_runnable(compute_plan: orchestrator.ComputePlan) -> bool:
    return compute_plan.status in _RUNNABLE_COMPUTE_PLAN_STATUSES


class _NonRunnableStatusError(RuntimeError):
    def __init__(self, status: str) -> None:
        self.status = status


class TaskNonRunnableStatusError(_NonRunnableStatusError):
    """The compute task status prevents running the task.

    Attributes:
        status: the status of the compute task.

    """


class ComputePlanNonRunnableStatusError(_NonRunnableStatusError):
    """The compute plan status prevents running the task.

    Attributes:
        status: the status of the compute plan.

    """


def _raise_if_task_not_runnable(
    task_key: str,
    client: orc_client.OrchestratorClient,
    allow_doing: bool = False,
    existing_task: ComputeTask = None,
) -> None:
    """Raise an exception if a compute task is not runnable by taking into account its status
    and the status of the associated compute plan.

    Args:
        task_key: the compute task key
        client: the orchestrator gRPC client.
        allow_doing: whether a compute task with the status DOING should be considered as runnable.
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

    if not _is_task_status_runnable(task, allow_doing):
        raise TaskNonRunnableStatusError(task.status.name)

    compute_plan = client.query_compute_plan(task.compute_plan_key)
    if not _is_compute_plan_status_runnable(compute_plan):
        raise ComputePlanNonRunnableStatusError(compute_plan.status.name)


def is_task_runnable(task_key: str, client: orc_client.OrchestratorClient, allow_doing: bool = False) -> bool:
    """Check whether a compute task is runnable given its status and the status of the associated compute plan.

    Args:
        task_key: the key of the compute task.
        client: the orchestrator gRPC client.
        allow_doing: whether a compute task with the status DOING should be considered as runnable.

    Returns:
        True if the compute task is runnable, False otherwise.

    """
    try:
        _raise_if_task_not_runnable(task_key, client, allow_doing)
    except (TaskNonRunnableStatusError, ComputePlanNonRunnableStatusError):
        return False
    else:
        return True


def abort_task_if_not_runnable(
    task_key: str, client: orc_client.OrchestratorClient, allow_doing: bool = False, task: ComputeTask = None
) -> None:
    """Cancel a compute task if its associated compute plan is not runnable. In addition, raise an error if the compute
    task is not runnable because of its status or the status of its compute plan.

    Args:
        task_key: the compute task key.
        client: the orchestrator gRPC client.
        allow_doing: whether a compute task with the status DOING should be considered as runnable.
        task: the compute task. if specified this task will be used to check the status instead of retrieving a task.

    Returns:
        None if the task is runnable.

    Raises:
        TaskNonRunnableStatusError: if the compute task is not runnable because of its status.
        ComputePlanNonRunnableStatusError: if the compute task is not runnable because the status
            of its associated compute plan.

    """
    try:
        _raise_if_task_not_runnable(task_key, client, allow_doing=allow_doing, existing_task=task)
    except ComputePlanNonRunnableStatusError as exc:
        logger.info("Compute plan not runnable. Canceling task.", compute_plan_status=exc.status)
        client.update_task_status(
            task_key,
            computetask_pb2.TASK_ACTION_CANCELED,
            log=f"Compute plan has a non-runnable status: {exc.status}",
        )
        raise


def start_task_if_not_started(task: ComputeTask, client: orc_client.OrchestratorClient) -> None:
    """Start a compute task if it is not already started

    Args:
        task: the compute task.
        client: the orchestrator gRPC client.

    Returns:
        None

    Raises:
        OrcError: if the status can't be updated to DOING
    """
    if task.status == ComputeTaskStatus.STATUS_TODO:
        try:
            logger.info("Updating task status to STATUS_DOING", task_key=task.key)
            client.update_task_status(task.key, computetask_pb2.TASK_ACTION_DOING)
        except OrcError as rpc_error:
            logger.exception(
                f"failed to update task status to DOING, {rpc_error.details}",
                task_key=task.key,
            )
            raise


def mark_as_done(task_key: str, client: orc_client.OrchestratorClient) -> None:
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

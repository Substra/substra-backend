import structlog

from orchestrator import client as orc_client
from orchestrator import computeplan_pb2
from orchestrator import computetask_pb2

_RUNNABLE_TASK_STATUSES = [computetask_pb2.STATUS_TODO]
_RUNNABLE_TASK_STATUSES = {computetask_pb2.ComputeTaskStatus.Name(s) for s in _RUNNABLE_TASK_STATUSES}
_NON_RUNNABLE_TASK_STATUSES = set(computetask_pb2.ComputeTaskStatus.keys()) - _RUNNABLE_TASK_STATUSES

_TASK_STATUS_DOING = computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.ComputeTaskStatus.STATUS_DOING)

_RUNNABLE_COMPUTE_PLAN_STATUSES = [computeplan_pb2.PLAN_STATUS_TODO, computeplan_pb2.PLAN_STATUS_DOING]
_RUNNABLE_COMPUTE_PLAN_STATUSES = {computeplan_pb2.ComputePlanStatus.Name(s) for s in _RUNNABLE_COMPUTE_PLAN_STATUSES}
_NON_RUNNABLE_COMPUTE_PLAN_STATUSES = set(computeplan_pb2.ComputePlanStatus.keys()) - _RUNNABLE_COMPUTE_PLAN_STATUSES

logger = structlog.get_logger(__name__)


def _is_task_status_runnable(task: dict, allow_doing: bool) -> bool:
    if allow_doing:
        return task["status"] in _RUNNABLE_TASK_STATUSES | {_TASK_STATUS_DOING}

    return task["status"] in _RUNNABLE_TASK_STATUSES


def _is_compute_plan_status_runnable(compute_plan: dict) -> bool:
    return compute_plan["status"] in _RUNNABLE_COMPUTE_PLAN_STATUSES


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


def raise_if_task_not_runnable(task_key: str, client: orc_client.OrchestratorClient, allow_doing: bool = False) -> None:
    """Raise an exception if a compute task is not runnable by taking into account its status
    and the status of the associated compute plan.

    Args:
        task_key: the key of the compute task.
        client: the orchestrator gRPC client.
        allow_doing: whether a compute task with the status DOING should be considered as runnable.

    Returns:
        None if the task is runnable.

    Raises:
        TaskNonRunnableStatusError: if the compute task is not runnable because of its status.
        ComputePlanNonRunnableStatusError: if the compute task is not runnable because the status
            of its associated compute plan.

    """
    task = client.query_task(task_key)
    if not _is_task_status_runnable(task, allow_doing):
        raise TaskNonRunnableStatusError(task["status"])

    compute_plan = client.query_compute_plan(task["compute_plan_key"])
    if not _is_compute_plan_status_runnable(compute_plan):
        raise ComputePlanNonRunnableStatusError(compute_plan["status"])


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
        raise_if_task_not_runnable(task_key, client, allow_doing)
    except (TaskNonRunnableStatusError, ComputePlanNonRunnableStatusError):
        return False
    else:
        return True


def abort_task_if_not_runnable(task_key: str, client: orc_client.OrchestratorClient, allow_doing: bool = False) -> None:
    """Cancel a compute task if its associated compute plan is not runnable. In addition, raise an error if the compute
    task is not runnable because of its status or the status of its compute plan.

    Args:
        task_key: the key of the compute task.
        client: the orchestrator gRPC client.
        allow_doing: whether a compute task with the status DOING should be considered as runnable.

    Returns:
        None if the task is runnable.

    Raises:
        TaskNonRunnableStatusError: if the compute task is not runnable because of its status.
        ComputePlanNonRunnableStatusError: if the compute task is not runnable because the status
            of its associated compute plan.

    """
    try:
        raise_if_task_not_runnable(task_key, client, allow_doing=allow_doing)
    except ComputePlanNonRunnableStatusError as exc:
        logger.info("Compute plan not runnable. Canceling task.", compute_plan_status=exc.status)
        client.update_task_status(
            task_key,
            computetask_pb2.TASK_ACTION_CANCELED,
            log=f"Compute plan has a non-runnable status: {exc.status}",
        )
        raise

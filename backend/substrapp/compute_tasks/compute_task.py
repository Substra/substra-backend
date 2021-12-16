import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.orchestrator import get_orchestrator_client


def is_task_runnable(channel_name: str, task_key: str, allow_doing: bool = False) -> bool:
    """
    Return True if the provided compute task is allowed to run based on its status and the status of the compute plan.

    Args:
        channel_name: the name of the channel.
        task_key: the compute task key.
        allow_doing: if True, allow the task to be run if it is in status 'doing'.
    """
    with get_orchestrator_client(channel_name) as client:
        task = client.query_task(task_key)
    return is_task_runnable_preloaded(channel_name, task, allow_doing)


def is_task_runnable_preloaded(channel_name: str, task: dict, allow_doing: bool = False) -> bool:
    """
    Return True if the provided compute task is allowed to run based on its status and the status of the compute plan.

    Args:
        channel_name: the name of the channel.
        task_key: the compute task key.
        allow_doing: if True, allow the task to be run if it is in status 'doing'.
    """
    allowed_task_statuses = [computetask_pb2.STATUS_TODO]
    allowed_cp_statuses = [computeplan_pb2.PLAN_STATUS_TODO, computeplan_pb2.PLAN_STATUS_DOING]

    if allow_doing:
        allowed_task_statuses.append(computetask_pb2.STATUS_DOING)

    task_status = computetask_pb2.ComputeTaskStatus.Value(task["status"])
    if task_status not in allowed_task_statuses:
        return False

    with get_orchestrator_client(channel_name) as client:
        cp = client.query_compute_plan(task["compute_plan_key"])

    cp_status = computeplan_pb2.ComputePlanStatus.Value(cp["status"])
    return cp_status in allowed_cp_statuses

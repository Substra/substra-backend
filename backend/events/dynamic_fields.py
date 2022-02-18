import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.event_pb2 as event_pb2
from localrep.models import ComputePlan
from orchestrator import client as orc_client


def add_cp_failed_task(compute_plan_key: str, client: orc_client.OrchestratorClient) -> None:
    compute_plan = ComputePlan.objects.get(key=compute_plan_key)

    if compute_plan.failed_task_key is not None:
        # failed_task field is already populated
        return

    first_failed_task = next(
        client.query_events_generator(
            event_kind=event_pb2.EVENT_ASSET_UPDATED,
            metadata={"status": "STATUS_FAILED", "compute_plan_key": compute_plan_key},
        ),
        None,
    )

    if first_failed_task is None:
        return

    # necessary call to retrieve the failed task category
    task_data = client.query_task(key=first_failed_task["asset_key"])

    compute_plan.failed_task_key = task_data["key"]
    compute_plan.failed_task_category = computetask_pb2.ComputeTaskCategory.Value(task_data["category"])
    compute_plan.save()

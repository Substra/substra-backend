from typing import Optional

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


def parse_computetask_dates_from_event(event: dict) -> tuple[Optional[str], Optional[str]]:
    """Parse start date or end date from computetask related event."""
    start_date, end_date = None, None
    # For a single event-sync, we cant equally use task status or event-status as the values are the same.
    # In case of all-assets re-sync, the task status contains only the last status.
    # If we want to retrieve start/end dates, we have to reassemble data from the event history.
    # This is why have to use event-status.
    status = computetask_pb2.ComputeTaskStatus.Value(event["metadata"]["status"])
    if status == computetask_pb2.STATUS_DOING:
        start_date = event["timestamp"]
    elif status in (
        computetask_pb2.STATUS_CANCELED,
        computetask_pb2.STATUS_DONE,
        computetask_pb2.STATUS_FAILED,
    ):
        end_date = event["timestamp"]
    return start_date, end_date


def fetch_error_type_from_event(event: dict, client: orc_client.OrchestratorClient) -> Optional[str]:
    error_type = None
    status = computetask_pb2.ComputeTaskStatus.Value(event["metadata"]["status"])
    if status == computetask_pb2.STATUS_FAILED:
        failure_report = client.get_failure_report({"compute_task_key": event["asset_key"]})
        if failure_report:
            error_type = failure_report["error_type"]
    return error_type


def add_cp_dates_and_duration(compute_plan_key: str) -> None:
    """Update start_date, end_date, duration fields."""

    compute_plan = ComputePlan.objects.get(key=compute_plan_key)

    if not compute_plan.start_date:
        first_started_task = compute_plan.compute_tasks.filter(start_date__isnull=False).order_by("start_date").first()
        if first_started_task:
            compute_plan.start_date = first_started_task.start_date

    ongoing_tasks = compute_plan.compute_tasks.filter(end_date__isnull=True).exists()
    if ongoing_tasks:
        compute_plan.end_date = None  # end date could be reset when cp is updated with new tasks
        compute_plan.duration = None
    else:
        last_ended_task = compute_plan.compute_tasks.filter(end_date__isnull=False).order_by("end_date").last()
        if last_ended_task:
            compute_plan.end_date = last_ended_task.end_date
            compute_plan.duration = (compute_plan.end_date - compute_plan.start_date).seconds

    compute_plan.save()

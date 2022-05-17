from typing import Optional

from localrep.models.computetask import ComputeTask
from orchestrator import client as orc_client


def parse_computetask_dates_from_event(event: dict) -> tuple[Optional[str], Optional[str]]:
    """Parse start date or end date from computetask related event."""
    start_date, end_date = None, None
    # For a single event-sync, we cant equally use task status or event-status as the values are the same.
    # In case of all-assets re-sync, the task status contains only the last status.
    # If we want to retrieve start/end dates, we have to reassemble data from the event history.
    # This is why have to use event-status.
    if event["metadata"]["status"] == ComputeTask.Status.STATUS_DOING:
        start_date = event["timestamp"]
    elif event["metadata"]["status"] in (
        ComputeTask.Status.STATUS_CANCELED,
        ComputeTask.Status.STATUS_DONE,
        ComputeTask.Status.STATUS_FAILED,
    ):
        end_date = event["timestamp"]
    return start_date, end_date


def fetch_failure_report_from_event(event: dict, client: orc_client.OrchestratorClient) -> Optional[str]:
    if event["metadata"]["status"] == ComputeTask.Status.STATUS_FAILED:
        return client.get_failure_report({"compute_task_key": event["asset_key"]})

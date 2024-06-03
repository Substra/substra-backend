from uuid import uuid4

import pytest
from django.utils import timezone

from api.events.sync import _on_create_failure_report_event
from api.events.sync import _on_create_performance_event
from api.models import ComputeTask
from api.models import ComputeTaskOutput
from api.models import Performance
from api.tests import asset_factory as factory
from substrapp.models import AssetFailureReport


@pytest.mark.django_db
def test_on_create_performance_event():
    compute_plan = factory.create_computeplan()

    metric = factory.create_function(
        outputs=factory.build_function_outputs(["performance"]),
    )
    test_task = factory.create_computetask(
        compute_plan,
        metric,
        outputs=factory.build_computetask_outputs(metric),
        status=ComputeTask.Status.STATUS_DONE,
    )

    # This is an ugly way to simulate the orchestrator event in order to
    # test the synchronization in a unit test.
    event = {
        "id": str(uuid4()),
        "channel": factory.DEFAULT_CHANNEL,
        "asset_key": str(uuid4()),
        "performance": {
            "compute_task_key": str(test_task.key),
            "compute_task_output_identifier": "performance",
            "creation_date": timezone.now(),
            "performance_value": 0.666,
        },
    }
    perf_event = event["performance"]

    _on_create_performance_event(event)

    task_output = ComputeTaskOutput.objects.get(
        task=perf_event["compute_task_key"],
        identifier=perf_event["compute_task_output_identifier"],
    )
    perf = Performance.objects.get(
        compute_task_output=task_output,
    )
    assert perf.value == perf_event["performance_value"]


@pytest.mark.django_db
def test_on_create_failure_report():
    compute_plan = factory.create_computeplan()

    function = factory.create_function(
        inputs=factory.build_function_inputs(["datasamples", "opener", "model"]),
        outputs=factory.build_function_outputs(["model"]),
        name="simple function",
    )
    test_task = factory.create_computetask(
        compute_plan,
        function,
        outputs=factory.build_computetask_outputs(function),
        status=ComputeTask.Status.STATUS_WAITING_FOR_PARENT_TASKS,
    )
    asset_key = test_task.key
    logs_address = "http://backend-org-1-substra-backend-server.org-1:8000/logs/b86cef85-90ca-4d7b-888e-98fa0f09f/file/"
    payload = {
        "id": "157ba2a7-e94c-4173-a647-45df4294e370",
        "asset_key": asset_key,
        "asset_kind": "ASSET_FAILURE_REPORT",
        "event_kind": "EVENT_ASSET_CREATED",
        "channel": "mychannel",
        "timestamp": "2024-01-09T17:20:25.994591Z",
        "failure_report": {
            "asset_key": asset_key,
            "error_type": "ERROR_TYPE_EXECUTION",
            "logs_address": {
                "checksum": "2fc783554c7e7eeb64a84f8547610ca2b7d4e8fefb1aab96200d2f3afe45e2d3",
                "storage_address": logs_address,
            },
            "creation_date": "2024-01-09T17:20:25.994591Z",
            "owner": "MyOrg1MSP",
            "asset_type": "FAILED_ASSET_COMPUTE_TASK",
        },
        "metadata": {},
    }
    _on_create_failure_report_event(payload)
    report = AssetFailureReport.objects.get(asset_key=asset_key)
    assert report.logs_address == logs_address
    compute_task = ComputeTask.objects.get(key=asset_key)
    assert compute_task.logs_address == logs_address
    assert compute_task.error_type == "ERROR_TYPE_EXECUTION"


@pytest.mark.django_db
def test_on_create_failure_report_internal():
    compute_plan = factory.create_computeplan()

    function = factory.create_function(
        inputs=factory.build_function_inputs(["datasamples", "opener", "model"]),
        outputs=factory.build_function_outputs(["model"]),
        name="simple function",
    )
    test_task = factory.create_computetask(
        compute_plan,
        function,
        outputs=factory.build_computetask_outputs(function),
        status=ComputeTask.Status.STATUS_WAITING_FOR_PARENT_TASKS,
    )
    asset_key = test_task.key
    payload = {
        "id": "157ba2a7-e94c-4173-a647-45df4294e370",
        "asset_key": asset_key,
        "asset_kind": "ASSET_FAILURE_REPORT",
        "event_kind": "EVENT_ASSET_CREATED",
        "channel": "mychannel",
        "timestamp": "2024-01-09T17:20:25.994591Z",
        "failure_report": {
            "asset_key": asset_key,
            "error_type": "ERROR_TYPE_INTERNAL",
            "creation_date": "2024-01-09T17:20:25.994591Z",
            "owner": "MyOrg1MSP",
            "asset_type": "FAILED_ASSET_COMPUTE_TASK",
        },
        "metadata": {},
    }
    _on_create_failure_report_event(payload)

    # AsseFailureReport is not created for internal errors
    with pytest.raises(AssetFailureReport.DoesNotExist):
        AssetFailureReport.objects.get(asset_key=asset_key)
    compute_task = ComputeTask.objects.get(key=asset_key)
    assert compute_task.error_type == "ERROR_TYPE_INTERNAL"

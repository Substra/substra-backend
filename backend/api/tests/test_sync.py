from uuid import uuid4

import pytest
from django.utils import timezone

from api.events.sync import _on_create_performance_event
from api.models import ComputeTask
from api.models import ComputeTaskOutput
from api.models import Performance
from api.tests import asset_factory as factory


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

    event = {
        "id": str(uuid4()),
        "channel": factory.DEFAULT_CHANNEL,
        "asset_key": str(uuid4()),
        "performance": {
            "compute_task_key": str(test_task.key),
            "compute_task_output_identifier": "performance",
            "metric_key": str(metric.key),
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
        metric__key=perf_event["metric_key"],
    )
    assert perf.value == perf_event["performance_value"]

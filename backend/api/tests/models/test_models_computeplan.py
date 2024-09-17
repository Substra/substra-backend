import pytest

from api.models import ComputeTask
from api.tests import asset_factory as factory


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status,has_end_date",
    (
        (ComputeTask.Status.STATUS_WAITING_FOR_BUILDER_SLOT, False),
        (ComputeTask.Status.STATUS_BUILDING, False),
        (ComputeTask.Status.STATUS_WAITING_FOR_PARENT_TASKS, False),
        (ComputeTask.Status.STATUS_WAITING_FOR_EXECUTOR_SLOT, False),
        (ComputeTask.Status.STATUS_EXECUTING, False),
        (ComputeTask.Status.STATUS_DONE, True),
        (ComputeTask.Status.STATUS_FAILED, True),
        (ComputeTask.Status.STATUS_CANCELED, True),
    ),
)
def test_update_end_date_single_task(status, has_end_date):
    function = factory.create_function()
    compute_plan = factory.create_computeplan()
    compute_task = factory.create_computetask(compute_plan, function, status=status)
    # validate inputs
    if has_end_date:
        assert compute_task.end_date is not None
    else:
        assert compute_task.end_date is None

    compute_plan.update_end_date()
    # validate outputs
    if has_end_date:
        assert compute_plan.end_date is not None
    else:
        assert compute_plan.end_date is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status,has_start_date",
    (
        (ComputeTask.Status.STATUS_WAITING_FOR_BUILDER_SLOT, False),
        (ComputeTask.Status.STATUS_BUILDING, True),
        (ComputeTask.Status.STATUS_WAITING_FOR_PARENT_TASKS, True),
        (ComputeTask.Status.STATUS_WAITING_FOR_EXECUTOR_SLOT, True),
        (ComputeTask.Status.STATUS_EXECUTING, True),
        (ComputeTask.Status.STATUS_DONE, True),
        (ComputeTask.Status.STATUS_FAILED, True),
        (ComputeTask.Status.STATUS_CANCELED, True),
    ),
)
def test_update_start_date_single_task(status, has_start_date):
    function = factory.create_function()
    compute_plan = factory.create_computeplan()
    compute_task = factory.create_computetask(compute_plan, function, status=status)
    # validate inputs
    if has_start_date:
        assert compute_task.start_date is not None
    else:
        assert compute_task.start_date is None

    compute_plan.update_status()
    # validate outputs
    if has_start_date:
        assert compute_plan.start_date is not None
    else:
        assert compute_plan.start_date is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status,has_end_date",
    (
        (ComputeTask.Status.STATUS_DONE, False),  # cp has restarted
        (ComputeTask.Status.STATUS_FAILED, True),
        (ComputeTask.Status.STATUS_CANCELED, True),
    ),
)
def test_update_end_date_ended_cp_with_ongoing_task(status, has_end_date):
    function = factory.create_function()
    compute_plan = factory.create_computeplan()
    factory.create_computetask(compute_plan, function, status=status)
    factory.create_computetask(compute_plan, function, status=ComputeTask.Status.STATUS_WAITING_FOR_PARENT_TASKS)

    compute_plan.update_end_date()
    # validate outputs
    if has_end_date:
        assert compute_plan.end_date is not None
    else:
        assert compute_plan.end_date is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status,has_start_date",
    (
        (ComputeTask.Status.STATUS_DONE, True),  # cp has restarted
        (ComputeTask.Status.STATUS_FAILED, True),
        (ComputeTask.Status.STATUS_CANCELED, True),
    ),
)
def test_update_start_date_ended_cp_with_ongoing_task(status, has_start_date):
    function = factory.create_function()
    compute_plan = factory.create_computeplan()
    factory.create_computetask(compute_plan, function, status=status)
    factory.create_computetask(compute_plan, function, status=ComputeTask.Status.STATUS_WAITING_FOR_PARENT_TASKS)

    compute_plan.update_status()
    # validate outputs
    if has_start_date:
        assert compute_plan.start_date is not None
    else:
        assert compute_plan.start_date is None

import pytest

from api.models import ComputeTask
from api.tests import asset_factory as factory


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status,has_start_date,has_end_date",
    (
        (ComputeTask.Status.STATUS_WAITING, False, False),
        (ComputeTask.Status.STATUS_TODO, False, False),
        (ComputeTask.Status.STATUS_DOING, True, False),
        (ComputeTask.Status.STATUS_DONE, True, True),
        (ComputeTask.Status.STATUS_FAILED, True, True),
        (ComputeTask.Status.STATUS_CANCELED, True, True),
    ),
)
def test_update_dates_single_task(status, has_start_date, has_end_date):
    function = factory.create_function()
    compute_plan = factory.create_computeplan()
    compute_task = factory.create_computetask(compute_plan, function, status=status)
    # validate inputs
    if has_start_date:
        assert compute_task.start_date is not None
    else:
        assert compute_task.start_date is None
    if has_end_date:
        assert compute_task.end_date is not None
    else:
        assert compute_task.end_date is None

    compute_plan.update_dates()
    # validate outputs
    if has_start_date:
        assert compute_plan.start_date is not None
    else:
        assert compute_plan.start_date is None
    if has_end_date:
        assert compute_plan.end_date is not None
    else:
        assert compute_plan.end_date is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status,has_start_date,has_end_date",
    (
        (ComputeTask.Status.STATUS_DONE, True, False),  # cp has restarted
        (ComputeTask.Status.STATUS_FAILED, True, True),
        (ComputeTask.Status.STATUS_CANCELED, True, True),
    ),
)
def test_update_dates_ended_cp_with_ongoing_task(status, has_start_date, has_end_date):
    function = factory.create_function()
    compute_plan = factory.create_computeplan()
    factory.create_computetask(compute_plan, function, status=status)
    factory.create_computetask(compute_plan, function, status=ComputeTask.Status.STATUS_WAITING)

    compute_plan.update_dates()
    # validate outputs
    if has_start_date:
        assert compute_plan.start_date is not None
    else:
        assert compute_plan.start_date is None
    if has_end_date:
        assert compute_plan.end_date is not None
    else:
        assert compute_plan.end_date is None

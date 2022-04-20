import pytest

import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.tests import factory


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status,has_start_date,has_end_date",
    (
        (computetask_pb2.STATUS_WAITING, False, False),
        (computetask_pb2.STATUS_TODO, False, False),
        (computetask_pb2.STATUS_DOING, True, False),
        (computetask_pb2.STATUS_DONE, True, True),
        (computetask_pb2.STATUS_FAILED, True, True),
        (computetask_pb2.STATUS_CANCELED, True, True),
    ),
)
def test_update_dates_single_task(status, has_start_date, has_end_date):
    algo = factory.create_algo()
    compute_plan = factory.create_computeplan()
    compute_task = factory.create_computetask(compute_plan, algo, status=status)
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
        (computetask_pb2.STATUS_DONE, True, False),  # cp has restarted
        (computetask_pb2.STATUS_FAILED, True, True),
        (computetask_pb2.STATUS_CANCELED, True, True),
    ),
)
def test_update_dates_ended_cp_with_ongoing_task(status, has_start_date, has_end_date):
    algo = factory.create_algo()
    compute_plan = factory.create_computeplan()
    factory.create_computetask(compute_plan, algo, status=status)
    factory.create_computetask(compute_plan, algo, status=computetask_pb2.STATUS_WAITING)

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

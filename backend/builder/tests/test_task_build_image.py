import time

import celery
import pytest

import orchestrator.mock as orc_mock
from builder.exceptions import BuildError
from builder.exceptions import BuildRetryError
from builder.tasks.tasks_build_image import build_image
from substrapp.compute_tasks.errors import CeleryNoRetryError
from substrapp.models import FailedAssetKind
from substrapp.utils.errors import store_failure

CHANNEL = "mychannel"


@pytest.mark.django_db
def test_store_failure_build_error():
    compute_task_key = "42ff54eb-f4de-43b2-a1a0-a9f4c5f4737f"
    msg = "Error building image"
    exc = BuildError(msg)

    failure_report = store_failure(
        exc, compute_task_key, FailedAssetKind.FAILED_ASSET_FUNCTION, error_type=BuildError.error_type.value
    )
    failure_report.refresh_from_db()

    assert str(failure_report.asset_key) == compute_task_key
    assert failure_report.logs.read() == str.encode(msg)


def test_catch_all_exceptions(celery_app, celery_worker, mocker):
    mocker.patch("builder.tasks.task.get_orchestrator_client")
    mocker.patch("builder.image_builder.image_builder.build_image_if_missing", side_effect=Exception("random error"))
    function = orc_mock.FunctionFactory()
    with pytest.raises(CeleryNoRetryError):
        r = build_image.apply_async(kwargs={"function_serialized": function.model_dump_json(), "channel_name": CHANNEL})
        r.get()


@pytest.mark.parametrize("execution_number", range(10))
def test_order_building_success(celery_app, celery_worker, mocker, execution_number):
    function_1 = orc_mock.FunctionFactory()
    function_2 = orc_mock.FunctionFactory()

    # BuildTask `before_start` uses this client to change the status, which would lead to `OrcError`
    mocker.patch("builder.tasks.task.get_orchestrator_client")
    mocker.patch("builder.image_builder.image_builder.build_image_if_missing", side_effect=lambda x, y: time.sleep(0.5))

    result_1 = build_image.apply_async(
        kwargs={"function_serialized": function_1.model_dump_json(), "channel_name": CHANNEL}
    )
    result_2 = build_image.apply_async(
        kwargs={"function_serialized": function_2.model_dump_json(), "channel_name": CHANNEL}
    )
    # get waits for the completion
    result_1.get()

    assert result_1.state == celery.states.SUCCESS
    assert result_2.state == "WAITING"


@pytest.mark.parametrize("execution_number", range(10))
def test_order_building_retry(celery_app, celery_worker, mocker, execution_number):
    function_retry = orc_mock.FunctionFactory()
    function_other = orc_mock.FunctionFactory()

    # Only retry once for function_retry
    def side_effect_creator():
        already_raised = False

        def side_effect(*args, **kwargs):
            nonlocal already_raised
            time.sleep(0.5)
            key = args[1].key
            if not already_raised and function_retry.key == key:
                already_raised = True
                raise BuildRetryError("random retriable error")

        return side_effect

    # BuildTask `before_start` uses this client to change the status, which would lead to `OrcError`
    mocker.patch("builder.tasks.task.get_orchestrator_client")
    mocker.patch("builder.image_builder.image_builder.build_image_if_missing", side_effect=side_effect_creator())

    result_retry = build_image.apply_async(
        kwargs={"function_serialized": function_retry.model_dump_json(), "channel_name": CHANNEL}
    )
    result_other = build_image.apply_async(
        kwargs={"function_serialized": function_other.model_dump_json(), "channel_name": CHANNEL}
    )

    result_retry.get()
    assert result_retry.state == celery.states.SUCCESS
    assert result_other.state == "WAITING"

import uuid

from pytest_mock import MockerFixture

import orchestrator.mock as orc_mock
from substrapp.tasks import tasks_compute_plan


def test_teardown_compute_plan_resources_cp_doing(mocker: MockerFixture):
    client = mocker.Mock()
    client.is_compute_plan_running.return_value = True
    mocked_teardown = mocker.patch("substrapp.tasks.tasks_compute_plan._teardown_pods_and_dirs")
    mocked_function_delete = mocker.patch("substrapp.tasks.tasks_compute_plan._delete_compute_plan_functions_images")

    cp_key = str(uuid.uuid4())

    tasks_compute_plan._teardown_compute_plan_resources(client, cp_key)

    client.is_compute_plan_running.assert_called_once()
    mocked_teardown.assert_not_called()
    mocked_function_delete.assert_not_called()


def test_teardown_compute_plan_resources_cp_done(mocker: MockerFixture):
    client = mocker.Mock()
    client.is_compute_plan_running.return_value = False
    mocked_teardown = mocker.patch("substrapp.tasks.tasks_compute_plan._teardown_pods_and_dirs")
    mocked_function_delete = mocker.patch("substrapp.tasks.tasks_compute_plan._delete_compute_plan_functions_images")

    cp_key = str(uuid.uuid4())

    tasks_compute_plan._teardown_compute_plan_resources(client, cp_key)

    client.is_compute_plan_running.assert_called_once()
    mocked_teardown.assert_called_once()
    mocked_function_delete.assert_called_once()


def test_delete_cp_function_images(mocker: MockerFixture):
    function_1_address = orc_mock.AddressFactory(checksum="azerty")
    function_2_address = orc_mock.AddressFactory(checksum="qwerty")
    functions = [
        orc_mock.FunctionFactory(function_address=function_1_address),
        orc_mock.FunctionFactory(function_address=function_2_address),
    ]
    mocked_delete_image = mocker.patch("substrapp.tasks.tasks_compute_plan.delete_container_image_safe")

    tasks_compute_plan._delete_compute_plan_functions_images(functions)

    mocked_delete_image.assert_any_call("function-azerty")
    mocked_delete_image.assert_any_call("function-qwerty")
    assert mocked_delete_image.call_count == 2

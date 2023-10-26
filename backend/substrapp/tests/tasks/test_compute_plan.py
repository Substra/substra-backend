import uuid

from pytest_mock import MockerFixture

from substrapp.tasks import tasks_compute_plan


def test_teardown_compute_plan_resources_cp_doing(mocker: MockerFixture):
    client = mocker.Mock()
    client.is_compute_plan_running.return_value = True
    mocked_teardown = mocker.patch("substrapp.tasks.tasks_compute_plan._teardown_pods_and_dirs")

    cp_key = str(uuid.uuid4())

    tasks_compute_plan._teardown_compute_plan_resources(client, cp_key)

    client.is_compute_plan_running.assert_called_once()
    mocked_teardown.assert_not_called()


def test_teardown_compute_plan_resources_cp_done(mocker: MockerFixture):
    client = mocker.Mock()
    client.is_compute_plan_running.return_value = False
    mocked_teardown = mocker.patch("substrapp.tasks.tasks_compute_plan._teardown_pods_and_dirs")

    cp_key = str(uuid.uuid4())

    tasks_compute_plan._teardown_compute_plan_resources(client, cp_key)

    client.is_compute_plan_running.assert_called_once()
    mocked_teardown.assert_called_once()

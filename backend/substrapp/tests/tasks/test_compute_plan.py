import uuid

from pytest_mock import MockerFixture

from substrapp.tasks import tasks_compute_plan


def test_teardown_compute_plan_resources_cp_doing(mocker: MockerFixture):
    client = mocker.Mock()
    client.is_compute_plan_doing.return_value = True
    mocked_teardown = mocker.patch("substrapp.tasks.tasks_compute_plan._teardown_pods_and_dirs")
    mocked_algo_delete = mocker.patch("substrapp.tasks.tasks_compute_plan._delete_compute_plan_algos_images")

    cp_key = str(uuid.uuid4())

    tasks_compute_plan._teardown_compute_plan_ressources(client, cp_key)

    client.is_compute_plan_doing.assert_called_once()
    mocked_teardown.assert_not_called()
    mocked_algo_delete.assert_not_called()


def test_teardown_compute_plan_resources_cp_done(mocker: MockerFixture):
    client = mocker.Mock()
    client.is_compute_plan_doing.return_value = False
    mocked_teardown = mocker.patch("substrapp.tasks.tasks_compute_plan._teardown_pods_and_dirs")
    mocked_algo_delete = mocker.patch("substrapp.tasks.tasks_compute_plan._delete_compute_plan_algos_images")

    cp_key = str(uuid.uuid4())

    tasks_compute_plan._teardown_compute_plan_ressources(client, cp_key)

    client.is_compute_plan_doing.assert_called_once()
    mocked_teardown.assert_called_once()
    mocked_algo_delete.assert_called_once()


def test_delete_cp_algo_images(mocker: MockerFixture):
    client = mocker.Mock()
    client.query_algos.return_value = [{"algorithm": {"checksum": "azerty"}}, {"algorithm": {"checksum": "qwerty"}}]
    mocked_delete_image = mocker.patch("substrapp.tasks.tasks_compute_plan.delete_container_image_safe")

    cp_key = str(uuid.uuid4())

    tasks_compute_plan._delete_compute_plan_algos_images(client, cp_key)

    mocked_delete_image.assert_any_call("algo-azerty")
    mocked_delete_image.assert_any_call("algo-qwerty")
    assert mocked_delete_image.call_count == 2

import datetime

import pytest
from django.test import override_settings
from django.urls.base import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedBackendClient
from api.tests.common import AuthenticatedClient

CHANNEL = "mychannel"
TEST_ORG = "MyTestOrg"

ORG_SETTINGS = {
    "LEDGER_CHANNELS": {"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    "LEDGER_MSP_ID": TEST_ORG,
}

EXTRA = {"HTTP_SUBSTRA_CHANNEL_NAME": CHANNEL, "HTTP_ACCEPT": "application/json;version=0.0"}
TASK_PROFILING_LIST_URL = reverse("api:task_profiling-list")


@override_settings(**ORG_SETTINGS)
class TaskProfilingViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self) -> None:
        function = factory.create_function()
        compute_plan = factory.create_computeplan()

        self.train_task = factory.create_computetask(compute_plan=compute_plan, function=function)

        factory.create_computetask_profiling(compute_task=self.train_task)

        self.expected_results = [
            {
                "compute_task_key": str(self.train_task.key),
                "execution_rundown": [{"duration": 10000000, "step": "step 1"}],
                "task_duration": None,
            }
        ]

    def test_task_profiling_list_success(self):
        response = self.client.get(TASK_PROFILING_LIST_URL)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_task_profiling_list_wrong_channel(self):
        self.client.channel = "yourchannel"
        response = self.client.get(TASK_PROFILING_LIST_URL)
        assert response.json() == {"count": 0, "next": None, "previous": None, "results": []}

    def test_task_profiling_retrieve_success(self):
        response = self.client.get(
            reverse("api:task_profiling-detail", args=[self.expected_results[0]["compute_task_key"]])
        )
        assert response.json() == self.expected_results[0]

    def test_task_profiling_create_bad_client(self):
        function = factory.create_function()
        cp = factory.create_computeplan()
        task = factory.create_computetask(compute_plan=cp, function=function)

        response = self.client.post(
            TASK_PROFILING_LIST_URL, {"compute_task_key": str(task.key), "channel": CHANNEL}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@override_settings(**ORG_SETTINGS)
class TaskProfilingViewTestsBackend(APITestCase):
    client_class = AuthenticatedBackendClient

    def test_task_profiling_create_success(self):
        function = factory.create_function()
        cp = factory.create_computeplan()
        task = factory.create_computetask(compute_plan=cp, function=function)

        response = self.client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(task.key)})
        assert response.status_code == status.HTTP_201_CREATED

        step_url = reverse("api:step-list", args=[str(task.key)])
        response = self.client.post(step_url, {"step": "custom_step", "duration": datetime.timedelta(seconds=20)})
        assert response.status_code == status.HTTP_200_OK
        
        expected_result = [
            {
                "compute_task_key": str(task.key),
                "execution_rundown": [{"duration": 20000000, "step": "custom_step"}],
                "task_duration": None,
            }
        ]

        response = self.client.get(TASK_PROFILING_LIST_URL, **EXTRA)
        assert response.json() == {
            "count": len(expected_result),
            "next": None,
            "previous": None,
            "results": expected_result,
        }

    def test_already_exist_task_profiling(self):
        function = factory.create_function()
        cp = factory.create_computeplan()
        task = factory.create_computetask(compute_plan=cp, function=function)

        response = self.client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(task.key)})
        assert response.status_code == status.HTTP_201_CREATED

        response = self.client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(task.key)})
        assert response.status_code == status.HTTP_409_CONFLICT


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_task_profiling_post_duplicate(authenticated_backend_client, create_compute_plan, create_compute_task):
    compute_plan = create_compute_plan()
    compute_task = create_compute_task(compute_plan)
    response = authenticated_backend_client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(compute_task.key)})
    assert response.status_code == status.HTTP_201_CREATED

    response = authenticated_backend_client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(compute_task.key)})
    assert response.status_code == status.HTTP_409_CONFLICT


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db(transaction=True)
def test_task_profiling_update_datetime(authenticated_backend_client, create_compute_plan, create_compute_task):
    compute_plan = create_compute_plan()
    compute_task = create_compute_task(compute_plan)

    authenticated_backend_client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(compute_task.key)})
    task_profiling = compute_task.task_profiling
    task_profiling.refresh_from_db()
    previous_datetime = task_profiling.creation_date

    profiling_url = reverse("api:task_profiling-detail", args=[str(compute_task.key)])
    authenticated_backend_client.put(profiling_url, {"compute_task_key": str(compute_task.key)}, **EXTRA)
    task_profiling.refresh_from_db()
    new_datetime = task_profiling.creation_date

    assert new_datetime > previous_datetime


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db()
def test_task_profiling_add_step_no_datetime_change(
    authenticated_backend_client, create_compute_plan, create_compute_task
):
    compute_plan = create_compute_plan()
    compute_task = create_compute_task(compute_plan)

    authenticated_backend_client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(compute_task.key)})
    task_profiling = compute_task.task_profiling
    task_profiling.refresh_from_db()
    previous_datetime = task_profiling.creation_date

    step_url = reverse("api:step-list", args=[str(compute_task.key)])
    authenticated_backend_client.post(step_url, {"compute_task_key": str(compute_task.key)})
    task_profiling.refresh_from_db()
    new_datetime = task_profiling.creation_date
    assert new_datetime == previous_datetime


@override_settings(
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    LEDGER_MSP_ID="other_org",
)
class TaskProfilingViewTestsOtherBackend(APITestCase):
    client_class = AuthenticatedBackendClient

    def setUp(self) -> None:
        self.url = reverse("api:task_profiling-list")

    def test_task_profiling_create_fail_other_backend(self):
        function = factory.create_function()
        cp = factory.create_computeplan()
        task = factory.create_computetask(compute_plan=cp, function=function)

        response = self.client.post(self.url, {"compute_task_key": str(task.key)})
        assert response.status_code == status.HTTP_403_FORBIDDEN

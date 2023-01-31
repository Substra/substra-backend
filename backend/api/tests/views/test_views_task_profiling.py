import datetime

from django.test import override_settings
from django.urls.base import reverse
from rest_framework.test import APITestCase

from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedBackendClient
from api.tests.common import AuthenticatedClient

CHANNEL = "mychannel"
TEST_ORG = "MyTestOrg"


@override_settings(
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    LEDGER_MSP_ID=TEST_ORG,
)
class TaskProfilingViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self) -> None:
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": CHANNEL, "HTTP_ACCEPT": "application/json;version=0.0"}
        self.url = reverse("api:task_profiling-list")

        function = factory.create_function()
        compute_plan = factory.create_computeplan()

        self.train_task = factory.create_computetask(compute_plan=compute_plan, function=function)

        factory.create_computetask_profiling(compute_task=self.train_task)

        self.expected_results = [
            {
                "compute_task_key": str(self.train_task.key),
                "execution_rundown": [{"duration": "00:00:10", "step": "step 1"}],
                "task_duration": None,
            }
        ]

    def test_task_profiling_list_success(self):
        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(self.expected_results), "next": None, "previous": None, "results": self.expected_results},
        )

    def test_task_profiling_list_wrong_channel(self):
        extra = {"HTTP_SUBSTRA_CHANNEL_NAME": "yourchannel", "HTTP_ACCEPT": "application/json;version=0.0"}
        response = self.client.get(self.url, **extra)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

    def test_task_profiling_retrieve_success(self):
        response = self.client.get(
            reverse("api:task_profiling-detail", args=[self.expected_results[0]["compute_task_key"]]),
            **self.extra,
        )
        self.assertEqual(response.json(), self.expected_results[0])

    def test_task_profiling_create_bad_client(self):
        function = factory.create_function()
        cp = factory.create_computeplan()
        task = factory.create_computetask(compute_plan=cp, function=function)

        response = self.client.post(self.url, {"compute_task_key": str(task.key), "channel": CHANNEL}, **self.extra)
        self.assertEqual(response.status_code, 403)


@override_settings(
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    LEDGER_MSP_ID=TEST_ORG,
)
class TaskProfilingViewTestsBackend(APITestCase):
    client_class = AuthenticatedBackendClient

    def setUp(self) -> None:
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": CHANNEL, "HTTP_ACCEPT": "application/json;version=0.0"}
        self.url = reverse("api:task_profiling-list")

    def test_task_profiling_create_success(self):
        function = factory.create_function()
        cp = factory.create_computeplan()
        task = factory.create_computetask(compute_plan=cp, function=function)

        response = self.client.post(self.url, {"compute_task_key": str(task.key)}, **self.extra)
        self.assertEqual(response.status_code, 201)

        step_url = reverse("api:step-list", args=[str(task.key)])
        response = self.client.post(
            step_url, {"step": "custom_step", "duration": datetime.timedelta(seconds=20)}, **self.extra
        )
        self.assertEqual(response.status_code, 200)

        expected_result = [
            {
                "compute_task_key": str(task.key),
                "execution_rundown": [{"duration": "00:00:20", "step": "custom_step"}],
                "task_duration": None,
            }
        ]

        response = self.client.get(self.url, **self.extra)
        self.assertEqual(
            response.json(),
            {"count": len(expected_result), "next": None, "previous": None, "results": expected_result},
        )

    def test_already_exist_task_profiling(self):
        function = factory.create_function()
        cp = factory.create_computeplan()
        task = factory.create_computetask(compute_plan=cp, function=function)

        response = self.client.post(self.url, {"compute_task_key": str(task.key)}, **self.extra)
        self.assertEqual(response.status_code, 201)

        response = self.client.post(self.url, {"compute_task_key": str(task.key)}, **self.extra)
        self.assertEqual(response.status_code, 201)


@override_settings(
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
    LEDGER_MSP_ID="other_org",
)
class TaskProfilingViewTestsOtherBackend(APITestCase):
    client_class = AuthenticatedBackendClient

    def setUp(self) -> None:
        self.extra = {"HTTP_SUBSTRA_CHANNEL_NAME": CHANNEL, "HTTP_ACCEPT": "application/json;version=0.0"}
        self.url = reverse("api:task_profiling-list")

    def test_task_profiling_create_fail_other_backend(self):
        function = factory.create_function()
        cp = factory.create_computeplan()
        task = factory.create_computetask(compute_plan=cp, function=function)

        response = self.client.post(self.url, {"compute_task_key": str(task.key)}, **self.extra)
        self.assertEqual(response.status_code, 403)

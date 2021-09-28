import mock
from unittest.mock import MagicMock
from rest_framework.test import APITestCase
from django.test import override_settings
from django_celery_results.models import TaskResult
from substrapp.tasks.tasks_prepare_task import prepare_task
from orchestrator.client import OrchestratorClient

CHANNEL = "mychannel"


@override_settings(LEDGER_CHANNELS={CHANNEL: {'chaincode': {'name': 'mycc'}, 'model_export_enabled': True}})
class PrepareTaskTests(APITestCase):
    def test_prepare_tasks(self):

        task = {"key": "subtuple_test", "compute_plan_key": "flkey", "status": "STATUS_TODO"}

        with mock.patch.object(TaskResult.objects, "filter") as mtaskresult, mock.patch(
            "substrapp.tasks.tasks_prepare_task.json.loads"
        ):

            mock_filter = MagicMock()
            mock_filter.count.return_value = 1
            mtaskresult.return_value = mock_filter

            with mock.patch.object(OrchestratorClient, "query_task", return_value=task), \
                 mock.patch("substrapp.tasks.tasks_prepare_task.compute_task.apply_async",
                            return_value="compute_task"), \
                 mock.patch.object(OrchestratorClient, "update_task_status"):
                prepare_task(CHANNEL, task)

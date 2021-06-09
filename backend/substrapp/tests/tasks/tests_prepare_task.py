import mock
from unittest.mock import MagicMock
from rest_framework.test import APITestCase
from django_celery_results.models import TaskResult
from substrapp.ledger.api import LedgerStatusError
from substrapp.tasks.tasks_prepare_task import prepare_task
from substrapp.compute_tasks.categories import TASK_CATEGORY_TRAINTUPLE

CHANNEL = "mychannel"


class PrepareTaskTests(APITestCase):
    def test_prepare_tasks(self):

        task = {"key": "subtuple_test", "compute_plan_key": "flkey", "status": "todo"}

        with mock.patch.object(TaskResult.objects, "filter") as mtaskresult, mock.patch(
            "substrapp.tasks.tasks_prepare_task.json.loads"
        ) as mjson_loads, mock.patch("substrapp.tasks.tasks_prepare_task._get_task_status") as mget_task_status:

            mock_filter = MagicMock()
            mock_filter.count.return_value = 1
            mtaskresult.return_value = mock_filter

            mget_task_status.return_value = "doing"
            mjson_loads.return_value = {"worker": "worker"}

            with mock.patch("substrapp.tasks.tasks_prepare_task.log_start_tuple") as mlog_start_tuple:
                mlog_start_tuple.side_effect = LedgerStatusError("Bad Response")
                prepare_task(CHANNEL, task, TASK_CATEGORY_TRAINTUPLE)

            with mock.patch("substrapp.tasks.tasks_prepare_task.log_start_tuple") as mlog_start_tuple, mock.patch(
                "substrapp.tasks.tasks_prepare_task.compute_task.apply_async"
            ) as mapply_async:
                mlog_start_tuple.return_value = "data", 201
                mapply_async.return_value = "compute_task"
                prepare_task(CHANNEL, task, TASK_CATEGORY_TRAINTUPLE)

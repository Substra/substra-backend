import mock
from celery.exceptions import Ignore
from django.test import override_settings
from rest_framework.test import APITestCase

from orchestrator.client import OrchestratorClient
from substrapp.tasks.tasks_prepare_task import prepare_task

CHANNEL = "mychannel"


@override_settings(LEDGER_CHANNELS={CHANNEL: {"chaincode": {"name": "mycc"}, "model_export_enabled": True}})
class PrepareTaskTests(APITestCase):
    def setUp(self):
        self.task = {
            "key": "subtuple_test",
            "compute_plan_key": "flkey",
            "status": "STATUS_TODO",
            "category": "TASK_TRAIN",
        }

    def test_task_is_not_runnable(self):
        doing_task = {
            "key": "subtuple_test",
            "compute_plan_key": "flkey",
            "status": "STATUS_DOING",
            "category": "TASK_TRAIN",
        }
        with mock.patch.object(OrchestratorClient, "query_task", return_value=doing_task), mock.patch(
            "celery.app.task.Task.request", new_callable=mock.PropertyMock
        ) as mrequest, mock.patch(
            "celery.worker.request.Request.delivery_info", new_callable=mock.PropertyMock
        ) as mdeliveryinfo:
            mrequest.return_value = mdeliveryinfo
            mdeliveryinfo.return_value = {"routing_key": "routing_key"}
            # task is already being processed this should return without performing further operation
            prepare_task(CHANNEL, self.task)

    def test_prepare_tasks_todo_orchestrator_error(self):
        with mock.patch.object(OrchestratorClient, "query_task", return_value=self.task), mock.patch(
            "celery.app.task.Task.request", new_callable=mock.PropertyMock
        ) as mrequest, mock.patch(
            "celery.worker.request.Request.delivery_info", new_callable=mock.PropertyMock
        ) as mdeliveryinfo, mock.patch.object(
            OrchestratorClient, "update_task_status"
        ) as mtask_status:
            mrequest.return_value = mdeliveryinfo
            mdeliveryinfo.return_value = {"routing_key": "routing_key"}
            mtask_status.side_effect = Exception("orchestrator error")
            with self.assertRaises(Ignore):
                prepare_task(CHANNEL, self.task)

    def test_prepare_tasks(self):
        with mock.patch.object(OrchestratorClient, "query_task", return_value=self.task), mock.patch(
            "substrapp.tasks.tasks_prepare_task.compute_task.apply_async", return_value="compute_task"
        ) as mapply_async, mock.patch(
            "celery.app.task.Task.request", new_callable=mock.PropertyMock
        ) as mrequest, mock.patch(
            "celery.worker.request.Request.delivery_info", new_callable=mock.PropertyMock
        ) as mdeliveryinfo, mock.patch.object(
            OrchestratorClient, "update_task_status"
        ):
            mrequest.return_value = mdeliveryinfo
            mdeliveryinfo.return_value = {"routing_key": "routing_key"}
            mapply_async.return_value = "compute_task"
            prepare_task(CHANNEL, self.task)

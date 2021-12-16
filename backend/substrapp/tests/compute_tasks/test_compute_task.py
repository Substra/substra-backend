from unittest import mock

from django.test import override_settings
from parameterized import parameterized
from rest_framework.test import APITestCase

import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
from orchestrator.client import OrchestratorClient
from substrapp.compute_tasks.compute_task import is_task_runnable

CHANNEL = "mychannel"


@override_settings(LEDGER_CHANNELS={CHANNEL: {"chaincode": {"name": "mycc"}, "model_export_enabled": True}})
class ComputeTaskTests(APITestCase):
    @parameterized.expand(
        [
            (
                "disallow_doing_task_todo_cp_todo",
                False,
                computetask_pb2.STATUS_TODO,
                computeplan_pb2.PLAN_STATUS_TODO,
                True,
            ),
            (
                "disallow_doing_task_doing_cp_doing",
                False,
                computetask_pb2.STATUS_DOING,
                computeplan_pb2.PLAN_STATUS_DOING,
                False,
            ),
            (
                "disallow_doing_todo_todo_cp_doing",
                False,
                computetask_pb2.STATUS_TODO,
                computeplan_pb2.PLAN_STATUS_DOING,
                True,
            ),
            (
                "disallow_doing_task_todo_cp_failed",
                False,
                computetask_pb2.STATUS_TODO,
                computeplan_pb2.PLAN_STATUS_FAILED,
                False,
            ),
            (
                "disallow_doing_task_failed_cp_todo",
                False,
                computetask_pb2.STATUS_FAILED,
                computeplan_pb2.PLAN_STATUS_TODO,
                False,
            ),
            (
                "allow_doing_task_todo_cp_todo",
                True,
                computetask_pb2.STATUS_TODO,
                computeplan_pb2.PLAN_STATUS_TODO,
                True,
            ),
            (
                "disallow_doing_task_doing_cp_doing",
                True,
                computetask_pb2.STATUS_DOING,
                computeplan_pb2.PLAN_STATUS_DOING,
                True,
            ),
            (
                "allow_doing_task_todo_cp_failed",
                True,
                computetask_pb2.STATUS_TODO,
                computeplan_pb2.PLAN_STATUS_FAILED,
                False,
            ),
            (
                "allow_doing_task_failed_cp_todo",
                True,
                computetask_pb2.STATUS_FAILED,
                computeplan_pb2.PLAN_STATUS_TODO,
                False,
            ),
            (
                "allow_doing_task_todo_cp_doing",
                True,
                computetask_pb2.STATUS_TODO,
                computeplan_pb2.PLAN_STATUS_DOING,
                True,
            ),
        ]
    )
    def test_is_task_runnable(self, _, allow_doing, task_status, cp_status, expected):
        task = {
            "compute_plan_key": "cp_key",
            "status": computetask_pb2.ComputeTaskStatus.Name(task_status),
        }

        cp = {
            "status": computeplan_pb2.ComputePlanStatus.Name(cp_status),
        }

        with (
            mock.patch.object(OrchestratorClient, "query_task", return_value=task),
            mock.patch.object(OrchestratorClient, "query_compute_plan", return_value=cp),
        ):

            actual = is_task_runnable(CHANNEL, "", allow_doing)
            self.assertEqual(expected, actual)

import tempfile
from unittest import mock

from django.test import override_settings
from grpc import RpcError
from grpc import StatusCode
from rest_framework.test import APITestCase

import orchestrator.computetask_pb2 as computetask_pb2
from orchestrator.client import OrchestratorClient
from substrapp.tasks.tasks_compute_task import compute_task

CHANNEL = "mychannel"


@override_settings(
    SUBTUPLE_DIR=tempfile.mkdtemp(),
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class ComputeTaskTests(APITestCase):
    def test_compute_task_exception(self):
        class FakeDirectories:
            compute_plan_dir = "fake/compute/plan/dir"

        class FakeContext:
            directories = FakeDirectories()
            compute_plan_key = "some compute plan key"
            task_category = computetask_pb2.TASK_TRAIN

        task = {
            "key": "some task key",
            "category": "TASK_TRAIN",
            "compute_plan_key": "some compute plan key",
            "in_models": None,
            "algo": {
                "key": "algo key",
                "algorithm": {
                    "checksum": "aa8d43bf6e3341b0034a2e396451ab731ccca95a4c1d4f65a4fcd30f9081ec7d",
                    "storage_address": "http://testserver/algo/17f98afc-2b82-4ce9-b232-1a471633d020/file/",
                },
            },
            "train": {"data_manager_key": "some data manager key"},
        }

        with mock.patch(
            "substrapp.tasks.tasks_compute_task.init_compute_plan_dirs"
        ) as minit_compute_plan_dirs, mock.patch(
            "substrapp.tasks.tasks_compute_task.init_task_dirs"
        ) as minit_task_dirs, mock.patch(
            "substrapp.tasks.tasks_compute_task.add_algo_to_buffer"
        ) as madd_algo_to_buffer, mock.patch(
            "substrapp.tasks.tasks_compute_task.add_task_assets_to_buffer"
        ) as madd_task_assets_to_buffer, mock.patch(
            "substrapp.tasks.tasks_compute_task.add_assets_to_taskdir"
        ) as madd_assets_to_taskdir, mock.patch(
            "substrapp.tasks.tasks_compute_task.restore_dir"
        ) as mrestore_dir, mock.patch(
            "substrapp.tasks.tasks_compute_task.build_images"
        ) as mbuild_images, mock.patch(
            "substrapp.tasks.tasks_compute_task.execute_compute_task"
        ) as mexecute_compute_task, mock.patch(
            "substrapp.tasks.tasks_compute_task.save_models"
        ) as msave_models, mock.patch(
            "substrapp.tasks.tasks_compute_task.commit_dir"
        ) as mcommit_dir, mock.patch(
            "substrapp.tasks.tasks_compute_task.teardown_task_dirs"
        ) as mteardown_task_dirs, mock.patch.object(
            OrchestratorClient, "register_performance"
        ) as mregister_performance, mock.patch.object(
            OrchestratorClient, "is_task_in_final_state", return_value=False
        ) as mis_task_in_final_state, mock.patch.object(
            OrchestratorClient, "query_compute_plan", return_value={}
        ), mock.patch.object(
            OrchestratorClient, "get_computetask_input_models"
        ), mock.patch.object(
            OrchestratorClient, "query_algo"
        ), mock.patch.object(
            OrchestratorClient, "query_datamanager"
        ):

            compute_task(CHANNEL, task, None)

            self.assertEqual(minit_compute_plan_dirs.call_count, 1)
            self.assertEqual(minit_task_dirs.call_count, 1)
            self.assertEqual(madd_algo_to_buffer.call_count, 1)
            self.assertEqual(madd_task_assets_to_buffer.call_count, 1)
            self.assertEqual(madd_assets_to_taskdir.call_count, 1)
            self.assertEqual(mrestore_dir.call_count, 1)
            self.assertEqual(mbuild_images.call_count, 1)
            self.assertEqual(mexecute_compute_task.call_count, 1)
            self.assertEqual(msave_models.call_count, 1)
            self.assertEqual(mcommit_dir.call_count, 1)
            self.assertEqual(mteardown_task_dirs.call_count, 1)
            self.assertEqual(mis_task_in_final_state.call_count, 1)

            error = RpcError()
            error.details = "OE0000"
            error.code = lambda: StatusCode.NOT_FOUND

            mregister_performance.side_effect = error
            compute_task(CHANNEL, task, None)

            with mock.patch.object(OrchestratorClient, "update_task_status"):
                mexecute_compute_task.side_effect = Exception("Test")
                with self.assertRaises(Exception) as exc:
                    compute_task(CHANNEL, task, None)
                self.assertEqual(str(exc.exception), "Test")

    def test_celery_retry(self):

        task = {
            "key": "some key",
            "compute_plan_key": None,
            "in_models": None,
            "category": computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_TEST),
        }

        with mock.patch.object(OrchestratorClient, "is_task_in_final_state", return_value=False), mock.patch(
            "substrapp.tasks.tasks_compute_task.Context.from_task"
        ), mock.patch("substrapp.tasks.tasks_compute_task.init_compute_plan_dirs"), mock.patch(
            "substrapp.tasks.tasks_compute_task.init_task_dirs"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.add_algo_to_buffer"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.add_task_assets_to_buffer"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.add_assets_to_taskdir"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.restore_dir"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.build_images"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.execute_compute_task"
        ) as mexecute_compute_task, mock.patch(
            "substrapp.tasks.tasks_compute_task.save_models"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.commit_dir"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.teardown_task_dirs"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.ComputeTask.retry"
        ) as mretry:

            mexecute_compute_task.side_effect = Exception("An exeption that should trigger retry mechanism")

            with self.assertRaises(Exception):
                compute_task(CHANNEL, task, None)

            self.assertEqual(mretry.call_count, 1)

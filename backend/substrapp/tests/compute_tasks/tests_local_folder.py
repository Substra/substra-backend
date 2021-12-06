import os
import tempfile
import uuid
from unittest import mock

from django.test import override_settings
from parameterized import parameterized
from rest_framework.test import APITestCase

import orchestrator.computetask_pb2 as computetask_pb2
from orchestrator.client import OrchestratorClient
from substrapp.compute_tasks.directories import CPDirName
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.tasks.tasks_compute_task import compute_task

MEDIA_ROOT = tempfile.mkdtemp()
CHANNEL = "mychannel"


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={CHANNEL: {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
)
class LocalFolderTests(APITestCase):
    @parameterized.expand([("without_exception", False), ("with_exception", True)])
    def test_local_folder(self, _, compute_job_raises):
        """
        This test ensures that changes to the subtuple local folder are reflected to the compute plan local folder iff
        the tuple execution succeeds.
        """

        compute_plan_key = str(uuid.uuid4())
        file = "model.txt"
        initial_value = "initial value"
        updated_value = "updated value"

        task = {
            "key": str(uuid.uuid4()),
            "compute_plan_key": compute_plan_key,
            "rank": 1,
            "algo": {"key": "some key", "checksum": "some checksum"},
            "category": computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_TRAIN),
        }

        class FakeDirectories:
            compute_plan_dir = tempfile.mkdtemp()
            task_dir = tempfile.mkdtemp()

        class FakeContext:
            directories = FakeDirectories()
            compute_plan_key = "some compute plan key"
            task_category = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_TRAIN)
            has_chainkeys = False

        ctx = FakeContext()

        local_folder = os.path.join(ctx.directories.task_dir, TaskDirName.Local)
        local_folder_committed = os.path.join(ctx.directories.compute_plan_dir, CPDirName.Local)

        # Write an initial value into the compute plan local folder
        os.makedirs(local_folder, exist_ok=True)
        os.makedirs(local_folder_committed, exist_ok=True)
        with open(os.path.join(local_folder_committed, file), "w") as x:
            x.write(initial_value)

        with mock.patch.object(OrchestratorClient, "is_task_in_final_state") as mis_task_in_final_state, mock.patch(
            "substrapp.tasks.tasks_compute_task.Context.from_task"
        ) as mfrom_task, mock.patch("substrapp.tasks.tasks_compute_task.init_asset_buffer"), mock.patch(
            "substrapp.tasks.tasks_compute_task.add_algo_to_buffer"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.add_task_assets_to_buffer"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.add_assets_to_taskdir"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.build_images"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.execute_compute_task"
        ) as mexecute_compute_task, mock.patch(
            "substrapp.tasks.tasks_compute_task.save_models"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.teardown_task_dirs"
        ):

            mis_task_in_final_state.return_value = False
            mfrom_task.return_value = FakeContext

            # The function `execute_compute_task` will:
            # 1. write a new value to the subtuple local folder
            # 2. and then:
            #    - complete successfully (compute_job_raises == False)
            #    - or raise an exception (compute_job_raises == True)

            def execute(*args, **kwargs):
                nonlocal local_folder
                with open(os.path.join(local_folder, file), "w") as x:
                    x.write(updated_value)
                if compute_job_raises:
                    raise Exception("I'm an error")

            mexecute_compute_task.side_effect = execute

            try:
                compute_task(CHANNEL, task, compute_plan_key)
            except Exception:
                if compute_job_raises:
                    # exception expected
                    pass

        # Check the compute plan local folder value is correct:
        # - If do_task did raise an exception then the local value should be unchanged
        # - If do_task did not raise an exception then the local value should be updated
        with open(os.path.join(local_folder_committed, file), "r") as x:
            content = x.read()
        self.assertEqual(content, initial_value if compute_job_raises else updated_value)

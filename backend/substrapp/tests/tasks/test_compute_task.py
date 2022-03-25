import errno
import io
import tempfile
from typing import Type
from unittest import mock

import pytest
from django.test import override_settings
from grpc import RpcError
from grpc import StatusCode
from rest_framework.test import APITestCase

import orchestrator.computetask_pb2 as computetask_pb2
from orchestrator.client import OrchestratorClient
from substrapp.compute_tasks import errors
from substrapp.tasks import tasks_compute_task
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
        ) as mregister_performance, mock.patch(
            "substrapp.compute_tasks.compute_task.raise_if_task_not_runnable"
        ) as mraise_if_task_not_runnable, mock.patch.object(
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
            self.assertEqual(madd_task_assets_to_buffer.call_count, 1)
            self.assertEqual(madd_assets_to_taskdir.call_count, 1)
            self.assertEqual(mrestore_dir.call_count, 1)
            self.assertEqual(mbuild_images.call_count, 1)
            self.assertEqual(mexecute_compute_task.call_count, 1)
            self.assertEqual(msave_models.call_count, 1)
            self.assertEqual(mcommit_dir.call_count, 1)
            self.assertEqual(mteardown_task_dirs.call_count, 1)
            self.assertEqual(mraise_if_task_not_runnable.call_count, 1)

            # test RPC error
            error = RpcError()
            error.details = "OE0000"
            error.code = lambda: StatusCode.NOT_FOUND

            mregister_performance.side_effect = error
            compute_task(CHANNEL, task, None)

            with mock.patch.object(OrchestratorClient, "update_task_status"):
                mexecute_compute_task.side_effect = Exception("Test")
                with self.assertRaises(errors.CeleryRetryError) as exc:
                    compute_task(CHANNEL, task, None)
                self.assertEqual(str(exc.exception.__cause__), "Test")

            # test not enough space on disk error
            mexecute_compute_task.side_effect = OSError(errno.ENOSPC, "No space left on device")
            with self.assertRaises(errors.CeleryRetryError) as exc:
                compute_task(CHANNEL, task, None)
            self.assertTrue("No space left on device" in str(exc.exception.__cause__))

            # test other OS error
            mexecute_compute_task.side_effect = OSError(errno.EACCES, "Dummy error")
            with self.assertRaises(errors.CeleryRetryError) as exc:
                compute_task(CHANNEL, task, None)
            self.assertTrue("Dummy error" in str(exc.exception.__cause__))

    def test_celery_retry(self):
        task = {
            "key": "some key",
            "compute_plan_key": None,
            "in_models": None,
            "category": computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_TEST),
        }

        with mock.patch("substrapp.compute_tasks.compute_task.raise_if_task_not_runnable"), mock.patch(
            "substrapp.tasks.tasks_compute_task.Context.from_task"
        ), mock.patch("substrapp.tasks.tasks_compute_task.init_compute_plan_dirs"), mock.patch(
            "substrapp.tasks.tasks_compute_task.init_task_dirs"
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
        ) as mretry, mock.patch(
            "substrapp.tasks.tasks_compute_task.clear_assets_buffer"
        ) as m_clear_assets_buffer:

            def basic_retry(exc, **retry_kwargs):
                # retry function that just re-raise the exception
                return exc

            # Explicitly set a side_effect for mretry that return an Exception,
            # otherwise mretry will be a MagicMock, which will make celery unhappy
            mretry.side_effect = basic_retry

            # retry because of generic exception
            exception_message = "an exception that should trigger the retry mechanism"
            mexecute_compute_task.side_effect = Exception(exception_message)

            with pytest.raises(errors.CeleryRetryError) as excinfo:
                compute_task(CHANNEL, task, None)

            assert str(excinfo.value.__cause__) == exception_message
            self.assertEqual(mretry.call_count, 1)

            # retry because no space left on device error
            mexecute_compute_task.side_effect = IOError(errno.ENOSPC, "no file left on device")

            with pytest.raises(errors.CeleryRetryError) as excinfo:
                compute_task(CHANNEL, task, None)

            assert "no file left on device" in str(excinfo.value.__cause__)

            self.assertEqual(mretry.call_count, 2)
            self.assertEqual(m_clear_assets_buffer.call_count, 1)

            # do not retry because the error happened in the compute pod
            mexecute_compute_task.side_effect = errors.ExecutionError("python not found", "Error while running command")

            with pytest.raises(errors.CeleryNoRetryError) as excinfo:
                compute_task(CHANNEL, task, None)

            assert "Error while running command" in str(excinfo.value)
            assert mretry.call_count == 2


@pytest.mark.django_db
@pytest.mark.parametrize("logs", [b"", b"Hello, World!"])
def test_store_failure_execution_error(logs: bytes):
    compute_task_key = "42ff54eb-f4de-43b2-a1a0-a9f4c5f4737f"
    exc = errors.ExecutionError(logs=io.BytesIO(logs))

    failure_report = tasks_compute_task._store_failure(exc, compute_task_key)
    failure_report.refresh_from_db()

    assert str(failure_report.compute_task_key) == compute_task_key
    assert failure_report.logs.read() == logs


@pytest.mark.parametrize("exc_class", [Exception, errors.BuildError])
def test_store_failure_ignored_exception(exc_class: Type[Exception]):
    assert tasks_compute_task._store_failure(exc_class(), "uuid") is None

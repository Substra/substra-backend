import mock

from django.test import override_settings
from rest_framework.test import APITestCase
from substrapp.compute_tasks.categories import TASK_CATEGORY_TRAINTUPLE

from substrapp.tasks.tasks_compute_task import compute_task
import tempfile

CHANNEL = "mychannel"


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ComputeTaskTests(APITestCase):
    def test_compute_task_exception(self):
        class FakeDirectories:
            compute_plan_dir = "fake/compute/plan/dir"

        class FakeContext:
            directories = FakeDirectories()
            compute_plan_key = "some compute plan key"
            task_category = TASK_CATEGORY_TRAINTUPLE

        task = {
            "key": "some task key",
            "compute_plan_key": "some compute plan key",
            "in_models": None,
            "algo": {"key": "algo key"},
        }

        with mock.patch("substrapp.tasks.tasks_compute_task.is_task_runnable") as mis_task_runnable, mock.patch(
            "substrapp.tasks.tasks_compute_task.Context.from_task"
        ) as mfrom_task, mock.patch(
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
        ) as mteardown_task_dirs, mock.patch(
            "substrapp.tasks.tasks_compute_task.log_success_tuple"
        ) as mlog_success_tuple:

            mis_task_runnable.return_value = True
            mfrom_task.return_value = FakeContext

            mlog_success_tuple.return_value = "data", 201
            compute_task(CHANNEL, TASK_CATEGORY_TRAINTUPLE, task, None)

            self.assertEqual(mfrom_task.call_count, 1)
            self.assertEqual(minit_compute_plan_dirs.call_count, 1)
            self.assertEqual(minit_task_dirs.call_count, 1)
            self.assertEqual(madd_algo_to_buffer.call_count, 1)
            self.assertEqual(madd_task_assets_to_buffer.call_count, 1)
            self.assertEqual(madd_assets_to_taskdir.call_count, 1)
            self.assertEqual(mrestore_dir.call_count, 2)  # local folder + chainkeys
            self.assertEqual(mbuild_images.call_count, 1)
            self.assertEqual(mexecute_compute_task.call_count, 1)
            self.assertEqual(msave_models.call_count, 1)
            self.assertEqual(mcommit_dir.call_count, 2)  # local folder + chainkeys
            self.assertEqual(mteardown_task_dirs.call_count, 1)

            mlog_success_tuple.return_value = "data", 404
            compute_task(CHANNEL, TASK_CATEGORY_TRAINTUPLE, task, None)

            with mock.patch("substrapp.tasks.tasks_compute_task.log_fail_tuple") as mlog_fail_tuple:
                mexecute_compute_task.side_effect = Exception("Test")
                mlog_fail_tuple.return_value = "data", 404
                with self.assertRaises(Exception) as exc:
                    compute_task(CHANNEL, TASK_CATEGORY_TRAINTUPLE, task, None)
                self.assertEqual(str(exc.exception), "Test")

    def test_celery_retry(self):
        subtuple_key = "test_owkin"
        subtuple = {"key": subtuple_key, "compute_plan_key": None, "in_models": None}

        with mock.patch("substrapp.tasks.tasks_compute_task.is_task_runnable") as mis_task_runnable, mock.patch(
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
            "substrapp.tasks.tasks_compute_task.log_success_tuple"
        ), mock.patch(
            "substrapp.tasks.tasks_compute_task.ComputeTask.retry"
        ) as mretry:

            mis_task_runnable.return_value = True
            mexecute_compute_task.side_effect = Exception("An exeption that should trigger retry mechanism")

            with self.assertRaises(Exception):
                compute_task(CHANNEL, "traintuple", subtuple, None)

            self.assertEqual(mretry.call_count, 1)

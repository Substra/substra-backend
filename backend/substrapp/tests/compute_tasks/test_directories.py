import os
import tempfile

from django.test import override_settings
from rest_framework.test import APITestCase

from substrapp.compute_tasks.directories import CPDirName
from substrapp.compute_tasks.directories import Directories
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.directories import init_compute_plan_dirs
from substrapp.compute_tasks.directories import init_task_dirs
from substrapp.compute_tasks.directories import teardown_compute_plan_dir
from substrapp.compute_tasks.directories import teardown_task_dirs

SUBTUPLE_DIR = tempfile.mkdtemp()


@override_settings(SUBTUPLE_DIR=SUBTUPLE_DIR)
class DirectoriesTests(APITestCase):
    test_file_name = "some_file"
    test_dir_name = "some_dir"

    def setUp(self):
        self.compute_plan_key = "<cp_key>"
        self.dirs = Directories(self.compute_plan_key)

    def test_init_compute_plan_dirs(self):
        init_compute_plan_dirs(self.dirs)
        for folder in CPDirName.All:
            path = os.path.join(os.path.join(SUBTUPLE_DIR, self.compute_plan_key, folder))
            self.assertTrue(os.path.exists(path), f"{path} should have been created")

        # Init a second time, it should not raise
        try:
            init_compute_plan_dirs(self.dirs)
        except Exception:
            self.fail("init_compute_plan_dirs raised Exception unexpectedly")

    def test_init_task_dirs(self):
        init_task_dirs(self.dirs)
        for folder in TaskDirName.All:
            path = os.path.join(os.path.join(SUBTUPLE_DIR, self.compute_plan_key, CPDirName.Task, folder))
            self.assertTrue(os.path.exists(path), f"{path} should have been created")

        # Init a second time, it should not raise
        try:
            init_task_dirs(self.dirs)
        except Exception:
            self.fail("init_task_dirs raised Exception unexpectedly")

    def test_teardown_task_dirs(self):
        init_task_dirs(self.dirs)

        for folder in TaskDirName.All:
            # create a file and a directory
            file_path = os.path.join(
                os.path.join(SUBTUPLE_DIR, self.compute_plan_key, CPDirName.Task, folder, self.test_file_name)
            )
            dir_path = os.path.join(
                os.path.join(SUBTUPLE_DIR, self.compute_plan_key, CPDirName.Task, folder, self.test_dir_name)
            )

            os.mkdir(dir_path)
            with open(file_path, "w") as f:
                f.write("test")

        teardown_task_dirs(self.dirs)

        for folder in TaskDirName.All:
            # check the file and directory have been deleted
            file_path = os.path.join(
                os.path.join(SUBTUPLE_DIR, self.compute_plan_key, CPDirName.Task, folder, self.test_file_name)
            )
            dir_path = os.path.join(
                os.path.join(SUBTUPLE_DIR, self.compute_plan_key, CPDirName.Task, folder, self.test_dir_name)
            )

            self.assertFalse(os.path.exists(file_path), f"{file_path} should not exist")
            self.assertFalse(os.path.exists(dir_path), f"{dir_path} should not exist")

        # Teardown a second time, it should not raise
        try:
            teardown_task_dirs(self.dirs)
        except Exception:
            self.fail("teardown_task_dirs raised Exception unexpectedly")

    def test_teardown_compute_plan_dir(self):
        init_compute_plan_dirs(self.dirs)
        self._create_compute_plan_test_files()
        teardown_compute_plan_dir(self.dirs)
        self._check_compute_plan_test_files_deleted()

        # Teardown a second time, it should not raise
        try:
            teardown_compute_plan_dir(self.dirs)
        except Exception:
            self.fail("teardown_task_dirs raised Exception unexpectedly")

    def _create_compute_plan_test_files(self):
        """Create a test file and a test folder in each compute plan subdirectory"""

        for folder in CPDirName.All:
            file_path = os.path.join(os.path.join(SUBTUPLE_DIR, self.compute_plan_key, folder, self.test_file_name))
            dir_path = os.path.join(os.path.join(SUBTUPLE_DIR, self.compute_plan_key, folder, self.test_dir_name))

            os.mkdir(dir_path)
            with open(file_path, "w") as f:
                f.write("test")

    def _check_compute_plan_test_files_deleted(self):
        """Paths should have been deleted"""

        for folder in CPDirName.All:
            # check the file and directory have been deleted
            file_path = os.path.join(os.path.join(SUBTUPLE_DIR, self.compute_plan_key, folder, self.test_file_name))
            dir_path = os.path.join(os.path.join(SUBTUPLE_DIR, self.compute_plan_key, folder, self.test_dir_name))

            self.assertFalse(os.path.exists(file_path), f"{file_path} should not exist")
            self.assertFalse(os.path.exists(dir_path), f"{dir_path} should not exist")

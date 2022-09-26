import os
import shutil
from shutil import copytree

import structlog
from django.conf import settings

from substrapp.utils import delete_dir
from substrapp.utils import remove_directory_contents

logger = structlog.get_logger(__name__)

SANDBOX_DIR = "/substra_internal"


# /var/medias/substra/subtuple     <- SUBTUPLE_DIR
# |
# ├── asset_buffer                 <- ASSET_BUFFER_DIR
# |   ├── data_samples
# |   ├── models
# |   └── openers
# |
# └── <compute_plan_key>           <- compute_plan_dir
#     ├── chainkeys
#     └── task                     <- task_dir
#         ├── chainkeys
#         ├── cli-args
#         ├── data_samples
#         ├── export
#         ├── in_models
#         ├── openers
#         ├── out_models
#         ├── perf
#         └── pred


class AssetBufferDirName:
    Datasamples = "data_samples"
    Models = "models"
    Openers = "openers"

    All = [Datasamples, Models, Openers]


class CPDirName:
    Chainkeys = "chainkeys"
    Task = "task"

    All = [Chainkeys, Task]


class TaskDirName:
    Chainkeys = "chainkeys"
    CliArgs = "cli-args"
    Datasamples = "data_samples"
    Export = "export"
    InModels = "in_models"
    Openers = "openers"
    OutModels = "out_models"
    Perf = "perf"

    All = [Chainkeys, CliArgs, Datasamples, Export, InModels, Openers, OutModels, Perf]


class Directories:
    """
    Directories is a helper to easily access the paths to folders
    used by a compute plan or a compute task.
    """

    compute_plan_key: str = None

    def __init__(self, compute_plan_key: str):
        self.compute_plan_key = compute_plan_key

    @property
    def compute_plan_dir(self) -> str:
        return os.path.join(settings.SUBTUPLE_DIR, self.compute_plan_key)

    @property
    def task_dir(self) -> str:
        return os.path.join(settings.SUBTUPLE_DIR, self.compute_plan_key, CPDirName.Task)


def init_compute_plan_dirs(dirs: Directories) -> None:
    os.makedirs(dirs.compute_plan_dir, exist_ok=True)
    for folder_name in CPDirName.All:
        os.makedirs(os.path.join(dirs.compute_plan_dir, folder_name), exist_ok=True)


def init_task_dirs(dirs: Directories) -> None:
    os.makedirs(dirs.task_dir, exist_ok=True)
    for folder_name in TaskDirName.All:
        dir = os.path.join(dirs.task_dir, folder_name)
        os.makedirs(dir, exist_ok=True)


def teardown_task_dirs(dirs: Directories) -> None:
    for folder_name in TaskDirName.All:
        # We can't delete the directory because it's mounted, instead, delete the _contents_
        dir = os.path.join(dirs.task_dir, folder_name)

        if os.path.exists(dir):
            remove_directory_contents(dir)
            logger.debug("Cleared directory", dir=dir)


def teardown_compute_plan_dir(dirs: Directories) -> None:
    logger.debug("Deleting compute plan directory", dir=dirs.compute_plan_dir)
    delete_dir(dirs.compute_plan_dir)


# Restore / Commit folders
#
# After a compute task succeeds, we:
# - commit the contents of the local folder to CPDirs.Local
# - commit the contents of the chainkeys folder to CPDirs.Chainkeys
#
# When a compute task fails, we discard the changes made by that task to the local folder and the chainkeys folder.
#
# Before a compute task starts, we:
# - Restore the local folder to TaskDir.Local
# - Restore the chainkeys folder to TaskDir.Chainkeys
#
# This mechanism allows us to ensure that if a task fails after making changes in the local folder / chainkeys folder,
# the next run of the same compute task (retry) will use a correct (committed) version of the local folder and the
# chainkeys folder, instead of a half-modified/corrupted folder.


def restore_dir(dirs: Directories, cp_folder: str, task_folder: str) -> None:
    """Copy the contents of a folder from compute_plan_dir to task_dir"""
    src = os.path.join(dirs.compute_plan_dir, cp_folder)
    dest = os.path.join(dirs.task_dir, task_folder)

    # We can't delete dst because it is mounted. Instead, empty it.
    if os.path.exists(dest):
        remove_directory_contents(dest)

    copytree(src, dest, dirs_exist_ok=True)


def commit_dir(dirs: Directories, task_folder: str, cp_folder: str) -> None:
    """Move the contents of a folder from task_dir to compute_dir"""
    src = os.path.join(dirs.task_dir, task_folder)
    dest = os.path.join(dirs.compute_plan_dir, cp_folder)

    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.mkdir(dest)

    # We can't mv src to dst because that would delete src, which is mounted. Instead, move the _contents_.
    file_names = os.listdir(src)
    for f in file_names:
        shutil.move(os.path.join(src, f), dest)

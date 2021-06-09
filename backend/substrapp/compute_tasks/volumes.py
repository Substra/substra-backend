import os
from typing import List
import logging
from django.conf import settings
from substrapp.compute_tasks.directories import Directories, SANDBOX_DIR, TaskDirName

logger = logging.getLogger(__name__)


def get_volumes(dirs: Directories):
    volume_mounts = []

    # /sandbox/chainkeys
    # /sandbox/datasamples
    # ...
    _add(volume_mounts, dirs.task_dir, TaskDirName.Chainkeys)
    _add(volume_mounts, dirs.task_dir, TaskDirName.Datasamples, read_only=True)
    _add(volume_mounts, dirs.task_dir, TaskDirName.Export)
    _add(volume_mounts, dirs.task_dir, TaskDirName.InModels, read_only=True)
    _add(volume_mounts, dirs.task_dir, TaskDirName.Local)
    _add(volume_mounts, dirs.task_dir, TaskDirName.Openers, read_only=True)
    _add(volume_mounts, dirs.task_dir, TaskDirName.OutModels)
    _add(volume_mounts, dirs.task_dir, TaskDirName.Pred)
    _add(volume_mounts, dirs.task_dir, TaskDirName.Perf)

    volumes = [
        {
            "name": "subtuple",
            "persistentVolumeClaim": {"claimName": settings.K8S_PVC["SUBTUPLE_PVC"]},
        }
    ]

    return volume_mounts, volumes


def _add(volume_mounts, task_dir: str, folder: str, read_only: bool = False):
    volume_mounts.append(
        {
            "name": "subtuple",
            "mountPath": os.path.join(SANDBOX_DIR, folder),
            "subPath": os.path.relpath(os.path.join(task_dir, folder), settings.SUBTUPLE_DIR),
            "readOnly": read_only,
        }
    )


def add_chainkeys_volume_mount(chainkeys_dir: str, volume_mounts: List[str]) -> None:
    volume_mounts.append(
        {
            "name": "subtuple",
            "mountPath": os.path.join(SANDBOX_DIR, "chainkeys"),
            "subPath": os.path.relpath(chainkeys_dir, settings.SUBTUPLE_DIR),
        }
    )

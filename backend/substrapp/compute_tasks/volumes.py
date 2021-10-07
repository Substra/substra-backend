import os
from django.conf import settings
from substrapp.compute_tasks.directories import Directories, SANDBOX_DIR, TaskDirName


def get_volumes(dirs: Directories, is_testtuple_eval: bool):
    volume_mounts = []

    # /sandbox/chainkeys
    # /sandbox/datasamples
    # ...
    _add(volume_mounts, dirs.task_dir, TaskDirName.Datasamples, read_only=True)
    _add(volume_mounts, dirs.task_dir, TaskDirName.Export)
    _add(volume_mounts, dirs.task_dir, TaskDirName.Openers, read_only=True)

    if is_testtuple_eval:
        # testtuple "evaluate"
        _add(volume_mounts, dirs.task_dir, TaskDirName.Pred, read_only=True)
        _add(volume_mounts, dirs.task_dir, TaskDirName.Perf)
    else:
        # testtuple "predict" and Xtraintuples
        _add(volume_mounts, dirs.task_dir, TaskDirName.Chainkeys)
        _add(volume_mounts, dirs.task_dir, TaskDirName.InModels, read_only=True)
        _add(volume_mounts, dirs.task_dir, TaskDirName.Local)
        _add(volume_mounts, dirs.task_dir, TaskDirName.OutModels)
        _add(volume_mounts, dirs.task_dir, TaskDirName.Pred)

    volumes = [
        {
            "name": "subtuple",
            "persistentVolumeClaim": {"claimName": settings.WORKER_PVC_SUBTUPLE},
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

import os

from django.conf import settings

from orchestrator import computetask_pb2
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import SANDBOX_DIR
from substrapp.compute_tasks.directories import TaskDirName


def get_volumes(ctx: Context):
    dirs = ctx.directories
    volume_mounts = []

    # /sandbox/chainkeys
    # /sandbox/datasamples
    # ...
    _add(volume_mounts, dirs.task_dir, TaskDirName.Datasamples, read_only=True)
    _add(volume_mounts, dirs.task_dir, TaskDirName.Export)
    _add(volume_mounts, dirs.task_dir, TaskDirName.InModels, read_only=True)
    _add(volume_mounts, dirs.task_dir, TaskDirName.Openers, read_only=True)

    if ctx.task_category == computetask_pb2.TASK_TEST:
        # testtuple
        _add(volume_mounts, dirs.task_dir, TaskDirName.Perf)
    else:
        # predicttuple and Xtraintuples
        _add(volume_mounts, dirs.task_dir, TaskDirName.Chainkeys)
        _add(volume_mounts, dirs.task_dir, TaskDirName.Local)
        _add(volume_mounts, dirs.task_dir, TaskDirName.OutModels)

    volumes = [
        {
            "name": "subtuple",
            "persistentVolumeClaim": {
                "claimName": settings.WORKER_PVC_SUBTUPLE
                if settings.WORKER_PVC_IS_HOSTPATH
                else get_worker_subtuple_pvc_name()
            },
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


def get_worker_subtuple_pvc_name():
    return f"{settings.WORKER_PVC_SUBTUPLE}-{os.getenv('HOSTNAME')}"


def get_docker_cache_pvc_name():
    return f"{settings.WORKER_PVC_DOCKER_CACHE}-{os.getenv('HOSTNAME')}"

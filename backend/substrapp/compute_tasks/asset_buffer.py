import os
import shutil
from functools import wraps
from typing import Callable

import structlog
from billiard import Process
from django.conf import settings

from orchestrator.resources import Address
from orchestrator.resources import DataManager
from orchestrator.resources import Model
from substrapp.clients import organization as organization_client
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import AssetBufferDirName
from substrapp.compute_tasks.directories import Directories
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.lock_local import lock_resource
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import get_dir_hash
from substrapp.utils import get_owner
from substrapp.utils import uncompress_content

logger = structlog.get_logger(__name__)

################
# ASSET BUFFER #
################
#
# The asset buffer keeps a copy of assets (data samples, openers, models).
#
# The asset buffer allows efficient reuse of assets resources: the assets are initially copied/downloaded to the asset
# buffer *only once*. Then the assets are made available to consumers (compute tasks) using the `link` command
# (hardlink), which is very fast. As a result, an asset is copied/downloaded *at most once*.
#
###########
# Workflow
###########
#
# - When a compute task starts, the buffer is populated to ensure it contains all the
#   assets (data samples, openers, models) necessary for the compute task. The assets
#   which are not already present in the buffer are loaded from the PVC or from
#   the network, and added to the buffer.
#
# - For each required asset, we then create a hardlink: the source is the asset path in the asset buffer directory, the
#   target is the asset path in the current task directory. The current task directory is then mounted (read-only) on
#   the compute pod.
#
# - When the compute task completes (success or error), the current task directory is cleared. As a result, the next
#   task starts with an empty environment, and cannot access the previous task's assets. Note that clearing the
#   current task directory means deleting the hardlinks. The assets in the buffer remain untouched.

LOCK_FETCH_ASSET_TTL = 60 * 60  # 1 hour


def init_asset_buffer() -> None:
    os.makedirs(settings.ASSET_BUFFER_DIR, exist_ok=True)
    for folder_name in AssetBufferDirName.All:
        os.makedirs(os.path.join(settings.ASSET_BUFFER_DIR, folder_name), exist_ok=True)


def clear_assets_buffer() -> None:
    for folder_name in AssetBufferDirName.All:
        folder = os.path.join(settings.ASSET_BUFFER_DIR, folder_name)
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except (OSError, shutil.Error) as e:
                # Intentionally don't raise. Keep on deleting from asset buffer.
                logger.exception("failed to delete asset from Asset Buffer", asset=file_path, e=e)


def add_to_buffer_safe(add_function) -> Callable:
    """
    Decorator to safely add an asset to the buffer.

    `add_function` must take a "dst" kwarg, corresponding to the destination path in the asset buffer.

    If the destination path already exists on disk, the function returns. Otherwise, add_function is called, then:
      - If add_function succeeds, a log is printed
      - If add_function raises, the destination path is deleted
    """

    @wraps(add_function)
    def wrap_function(*args, **kwargs):
        dst = kwargs["dst"]

        if os.path.exists(dst):
            return  # asset already exists

        try:
            add_function(*args, **kwargs)
        except Exception as e:
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)
            raise e
        else:
            _log_added(dst)

    wrap_function.is_asset_buffer_safe = True
    return wrap_function


def add_task_assets_to_buffer(ctx: Context) -> None:
    """
    Copy/Download assets (data samples, openers, models) to the asset buffer.

    Assets which are already present in the asset buffer are not copied/downloaded again.

    Each file download is protected with a lock to ensure there is no concurrent access
    to a single asset (see issue #570). This is needed as multiple Compute Plans may depend
    on the same input assets.
    """

    # Data samples
    for data_sample_key in ctx.data_sample_keys:
        with lock_resource("data_sample", data_sample_key, ttl=LOCK_FETCH_ASSET_TTL):
            _add_datasample_to_buffer(data_sample_key)

    # Openers
    if ctx.data_manager:
        with lock_resource("opener", ctx.data_manager.key, ttl=LOCK_FETCH_ASSET_TTL):
            _add_opener_to_buffer(ctx.channel_name, ctx.data_manager)

    # In-models
    if ctx.input_models:
        # As models are downloaded in subprocesses, the lock is done in the subprocess directly
        _add_models_to_buffer(ctx.channel_name, ctx.input_models)


def add_model_from_path(model_path: str, model_key: str) -> None:
    """
    Save a model computed by a compute task to the asset buffer.

    Unlike other assets, out-models are *new* assets that weren't previously present in the asset buffer.
    """
    dst = os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Models, model_key)
    os.rename(model_path, dst)
    _log_added(dst)


def add_assets_to_taskdir(ctx: Context) -> None:

    dirs = ctx.directories

    _add_assets_to_taskdir(dirs, AssetBufferDirName.Datasamples, TaskDirName.Datasamples, ctx.data_sample_keys)

    if ctx.data_manager:
        _add_assets_to_taskdir(dirs, AssetBufferDirName.Openers, TaskDirName.Openers, [ctx.data_manager.key])

    if ctx.input_models:
        _add_assets_to_taskdir(
            dirs, AssetBufferDirName.Models, TaskDirName.InModels, [model.key for model in ctx.input_models]
        )


def delete_models_from_buffer(model_keys: list[str]) -> None:
    for model_key in model_keys:
        model_path = os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Models, model_key)
        if os.path.exists(model_path):
            os.remove(model_path)


def _add_datasample_to_buffer(data_sample_key: str) -> None:
    """Copy data sample to the asset buffer"""
    dst = os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Datasamples, data_sample_key)
    _add_datasample_to_buffer_internal(data_sample_key, dst=dst)


@add_to_buffer_safe
def _add_datasample_to_buffer_internal(data_sample_key: str, dst: str) -> None:
    from substrapp.models import DataSample

    data_sample = DataSample.objects.get(key=data_sample_key)

    if data_sample.file:
        # add from storage
        content = data_sample.file.read()
        data_sample.file.close()
        uncompress_content(content, dst)
    elif not settings.ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS:
        # the `datasample.path` field is filled but Server Media is not available.
        # it is not possible to retrieve datasamples
        raise Exception(f"Server Media usage is disabled, Data Sample ({data_sample_key}) cannot be retrieved")
    else:
        # add from servermedias
        if not os.path.exists(data_sample.path) or not os.path.isdir(data_sample.path):
            raise Exception(f"Data Sample ({data_sample.path}) is missing in local storage")
        if not os.listdir(data_sample.path):
            raise Exception(f"Data Sample ({data_sample.path}) is empty in local storage")
        shutil.copytree(data_sample.path, dst)

    # verify checksum
    checksum = get_dir_hash(dst)
    if checksum != data_sample.checksum:
        shutil.rmtree(os.path.dirname(dst))
        raise Exception(f"Data Sample ({data_sample_key}) checksum in tuple is not the same as in local db")


def _add_opener_to_buffer(channel_name: str, data_manager: DataManager) -> None:
    """Copy opener to the asset buffer"""

    dst = os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Openers, data_manager.key)
    _add_opener_to_buffer_internal(channel_name, data_manager.opener, dst=dst)


@add_to_buffer_safe
def _add_opener_to_buffer_internal(channel_name: str, opener: Address, dst: str) -> None:
    os.mkdir(dst)
    organization_client.download(
        channel_name, get_owner(), opener.uri, os.path.join(dst, Filenames.Opener), opener.checksum
    )


def _add_models_to_buffer(channel_name: str, models: list[Model]) -> None:
    """Copy/Download models to the asset buffer"""

    # Close django connection to force each Process to create its own as
    # django orm connection is not fork safe https://code.djangoproject.com/ticket/20562
    from django import db

    db.connections.close_all()

    procs = []
    exceptions = []

    for model in models:
        with get_orchestrator_client(channel_name) as client:
            parent_task = client.query_task(model.compute_task_key)
        args = (channel_name, model, parent_task.worker)
        proc = Process(target=_add_model_to_buffer_with_lock, args=args)
        procs.append((proc, args))
        proc.start()

    for proc, args in procs:
        proc.join()
        if proc.exitcode != 0:
            exceptions.append(Exception(f"fetch model failed for args {args}"))

    # Close django old connections to avoid potential leak
    db.close_old_connections()
    if exceptions:
        # avoid partial model download
        delete_models_from_buffer([model.key for model in models])
        raise Exception(exceptions)


def _add_model_to_buffer(channel_name: str, model: Model, organization_id: str) -> None:
    dst = os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Models, model.key)
    _add_model_to_buffer_internal(channel_name, model, organization_id, dst=dst)


@add_to_buffer_safe
def _add_model_to_buffer_internal(channel_name: str, model: Model, organization_id: str, dst: str) -> None:
    organization_client.download(
        channel_name,
        organization_id,
        model.address.uri,
        dst,
        model.address.checksum,
        salt=model.compute_task_key,
    )


def _add_model_to_buffer_with_lock(channel_name: str, model: Model, organization_id: str) -> None:
    with lock_resource("model", model.key, ttl=LOCK_FETCH_ASSET_TTL):
        return _add_model_to_buffer(channel_name, model, organization_id)


def _add_assets_to_taskdir(dirs: Directories, b_dir: str, t_dir: str, keys: list[str]):
    """
    Create a hardlink for the asset.

    The source is the asset path in the buffer directory.
    The target is the asset path in the current task directory.
    """
    for key in keys:
        src = os.path.join(settings.ASSET_BUFFER_DIR, b_dir, key)
        dst = os.path.join(dirs.task_dir, t_dir, key)

        logger.debug("Create hardlink", src=src, dst=dst)

        if os.path.exists(dst):
            shutil.rmtree(dst)

        if os.path.isdir(src):
            # We cannot hardlink directories. Replicate the folder hierarchy, and hardlink files.
            shutil.copytree(src, dst, copy_function=os.link)
        else:
            os.link(src, dst)


def _log_added(path: str) -> None:
    logger.debug("Added to buffer", path=path)

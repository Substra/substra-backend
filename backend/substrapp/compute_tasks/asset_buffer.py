import os
import logging
import shutil
from django.conf import settings
from typing import List, Dict
from billiard import Process
from substrapp.compute_tasks.categories import (
    TASK_CATEGORY_TRAINTUPLE,
    TASK_CATEGORY_AGGREGATETUPLE,
    TASK_CATEGORY_COMPOSITETRAINTUPLE,
    TASK_CATEGORY_TESTTUPLE,
)
from substrapp.compute_tasks.directories import Directories, TaskDirName, AssetBufferDirName
from substrapp.compute_tasks.context import Context
from substrapp.ledger.api import get_object_from_ledger
from substrapp.compute_tasks.command import (
    get_composite_traintuple_out_models,
    get_traintuple_out_model,
    Filenames,
)
from substrapp.utils import (
    get_dir_hash,
    get_hash,
    get_and_put_asset_content,
    timeit,
    uncompress_content,
    get_asset_content,
    create_directory,
)

logger = logging.getLogger(__name__)

################
# ASSET BUFFER #
################
#
# The asset buffer keeps a copy of assets (data samples, openers, models).
#
# The asset buffer allows efficient reuse of assets resources: the assets are initially copied/downloaded to the asset
# buffer *only once*. Then the assets are made available to consumers (comupute tasks) using the `link` command
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


def init_asset_buffer() -> None:
    create_directory(settings.ASSET_BUFFER_DIR)
    for folder_name in AssetBufferDirName.All:
        create_directory(os.path.join(settings.ASSET_BUFFER_DIR, folder_name))


@timeit
def add_algo_to_buffer(ctx: Context) -> None:
    """
    Download the algo to the asset buffer.

    If the algo is already present in the asset buffer, skip the download.
    """
    task = ctx.task
    task_category = ctx.task_category
    dst = ctx.algo_docker_context_dir

    if os.path.exists(dst):
        # algo already exists
        return

    task_category = task["traintuple_type"] if task_category == TASK_CATEGORY_TESTTUPLE else task_category
    content = _download_algo(ctx.channel_name, task_category, ctx.algo_key)
    uncompress_content(content, dst)


@timeit
def add_metrics_to_buffer(ctx: Context) -> None:
    """
    Download the metrics to the asset buffer.

    If the metrics is already present in the asset buffer, skip the download.
    """
    dst = ctx.metrics_docker_context_dir

    if os.path.exists(dst):
        # metrics already exists
        return

    metrics_content = _download_objective(ctx.channel_name, ctx.objective_key)
    uncompress_content(metrics_content, dst)


def add_task_assets_to_buffer(ctx: Context) -> None:
    """
    Copy/Download assets (data samples, openers, models) to the asset buffer.

    Assets which are already present in the asset buffer are not copied/downloaded again.
    """
    task = ctx.task

    # Data samples
    data_sample_keys = _get_task_data_sample_keys(task)
    if data_sample_keys:
        _add_datasamples_to_buffer(data_sample_keys)

    # Openers
    dataset_key = _get_task_dataset_key(task)
    if dataset_key:
        _add_opener_to_buffer(dataset_key, task["dataset"]["opener_checksum"])

    # In-models
    models = _get_task_models(ctx.channel_name, task, ctx.task_category)
    if models:
        _add_models_to_buffer(ctx.channel_name, models)


def add_model_from_path(model_path: str, model_key: str) -> None:
    """
    Save a model computed by a compute task to the asset buffer.

    Unlike other assets (handled by `move_task_assets_from_taskdir_to_buffer`), out-models are *new* assets that
    weren't previously present in the asset buffer.
    """
    dst = os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Models, model_key)
    os.rename(model_path, dst)
    _log_added(dst)


def add_assets_to_taskdir(ctx: Context) -> None:

    dirs = ctx.directories
    task = ctx.task
    task_category = ctx.task_category

    data_sample_keys = _get_task_data_sample_keys(task)
    if data_sample_keys:
        _add_assets_to_taskdir(dirs, AssetBufferDirName.Datasamples, TaskDirName.Datasamples, data_sample_keys)

    dataset_key = _get_task_dataset_key(task)
    if dataset_key:
        _add_assets_to_taskdir(dirs, AssetBufferDirName.Openers, TaskDirName.Openers, [dataset_key])

    models = _get_task_models(ctx.channel_name, task, task_category)
    if models:
        _add_assets_to_taskdir(
            dirs, AssetBufferDirName.Models, TaskDirName.InModels, [model["key"] for model in models]
        )


def delete_models_from_buffer(model_keys: List[str]) -> None:
    for model_key in model_keys:
        model_path = os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Models, model_key)
        if os.path.exists(model_path):
            os.remove(model_path)


def _add_datasamples_to_buffer(data_sample_keys: List[str]) -> None:
    """Copy data samples to the asset buffer"""
    from substrapp.models import DataSample

    for key in data_sample_keys:

        dst = os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Datasamples, key)

        if os.path.exists(dst):
            # asset already exists
            return

        data_sample = DataSample.objects.get(key=key)

        if not os.path.exists(data_sample.path) or not os.path.isdir(data_sample.path):
            raise Exception(f"Data Sample ({data_sample.path}) is missing in local storage")

        if not os.listdir(data_sample.path):
            raise Exception(f"Data Sample ({data_sample.path}) is empty in local storage")

        data_sample_checksum = get_dir_hash(data_sample.path)
        if data_sample_checksum != data_sample.checksum:
            raise Exception("Data Sample checksum in tuple is not the same as in local db")

        shutil.copytree(data_sample.path, dst)
        _log_added(dst)


def _add_opener_to_buffer(dataset_key: str, opener_checksum: str) -> None:
    """Copy opener to the asset buffer"""
    from substrapp.models import DataManager

    dst = os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Openers, dataset_key, Filenames.Opener)

    if os.path.exists(dst):
        # asset already exists
        return

    datamanager = DataManager.objects.get(key=dataset_key)

    if not os.path.exists(datamanager.data_opener.path) or not os.path.isfile(datamanager.data_opener.path):
        raise Exception(f"DataOpener file ({datamanager.data_opener.path}) is missing in local storage")

    if get_hash(datamanager.data_opener.path) != opener_checksum:
        raise Exception("DataOpener checksum in Subtuple is not the same as in local db")

    os.makedirs(os.path.dirname(dst))
    shutil.copy(datamanager.data_opener.path, dst)
    _log_added(dst)


def _add_models_to_buffer(channel_name: str, models: List[Dict]) -> None:
    """Copy/Download models to the asset buffer"""

    # Close django connection to force each Process to create its own as
    # django orm connection is not fork safe https://code.djangoproject.com/ticket/20562
    from django import db

    db.connections.close_all()

    procs = []
    exceptions = []

    for model in models:
        args = (channel_name, model)
        proc = Process(target=_add_model_to_buffer, args=args)
        procs.append((proc, args))
        proc.start()

    for proc, args in procs:
        proc.join()
        if proc.exitcode != 0:
            exceptions.append(Exception(f"fetch model failed for args {args}"))

    # Close django old connections to avoid potential leak
    db.close_old_connections()
    if exceptions:
        raise Exception(exceptions)


def _add_model_to_buffer(channel_name: str, model: Dict) -> None:
    from substrapp.models import Model

    dst = os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Models, model["key"])

    if os.path.exists(dst):
        # asset already exists
        return

    if "storage_address" in model and model["storage_address"]:
        tuple_type, metadata = _find_training_step_tuple_from_key(channel_name, model["traintuple_key"])
        node_id = _get_tuple_owner(tuple_type, metadata)

        get_and_put_asset_content(
            channel_name, model["storage_address"], node_id, model["checksum"], dst, model["traintuple_key"]
        )

    else:  # head model
        m = Model.objects.get(key=model["key"])

        if not os.path.exists(m.file.path) or not os.path.isfile(m.file.path):
            raise Exception(f"Model file ({m.file.path}) is missing in local storage")

        if get_hash(m.file.path, model["traintuple_key"]) != m.checksum:
            raise Exception("Model checksum in Subtuple is not the same as in local db")

        shutil.copy(m.file.path, dst)

    _log_added(dst)


def _get_tuple_owner(tuple_type, tuple_):
    # TODO orchestrator: burn with fire
    if tuple_type == TASK_CATEGORY_AGGREGATETUPLE:
        return tuple_["worker"]
    return tuple_["dataset"]["worker"]


def _add_assets_to_taskdir(dirs: Directories, b_dir: str, t_dir: str, keys: List[str]):
    """
    Create a hardlink for the asset.

    The source is the asset path in the buffer directory.
    The target is the asset path in the current task directory.
    """
    for key in keys:
        src = os.path.join(settings.ASSET_BUFFER_DIR, b_dir, key)
        dst = os.path.join(dirs.task_dir, t_dir, key)

        if os.path.isdir(src):
            # We cannot hardlink directories. Replicate the folder hierarchy, and hardlink files.
            for dir, _, files in os.walk(src):
                dst_dir = os.path.abspath(os.path.join(dst, os.path.relpath(dir, src)))
                logger.debug(f"Create folder {dst_dir}")
                os.mkdir(dst_dir)
                for f in files:
                    src_file = os.path.join(dir, f)
                    dst_file = os.path.join(dst_dir, f)
                    logger.debug(f"Create hardlink {src_file} -> {dst_file}")
                    os.link(src_file, dst_file)
        else:
            logger.debug(f"Create hardlink {src} -> {dst}")
            os.link(src, dst)


def _get_task_data_sample_keys(task) -> List[str]:
    if "dataset" in task and "data_sample_keys" in task["dataset"]:
        return task["dataset"]["data_sample_keys"]
    return []


def _get_task_dataset_key(task) -> str:
    if "dataset" in task:
        return task["dataset"]["key"]
    return None


def _get_task_models(channel_name: str, task: Dict, task_category: str) -> List[str]:
    # TODO orchestrator: what a nightmare, bring the gasoline tanks please
    if task_category == TASK_CATEGORY_TRAINTUPLE:
        return [_get_traintuple_out_model(channel_name, model["traintuple_key"]) for model in (task["in_models"] or [])]
    elif task_category == TASK_CATEGORY_TESTTUPLE:
        if task["traintuple_type"] == TASK_CATEGORY_COMPOSITETRAINTUPLE:
            head_model, trunk_model = get_composite_traintuple_out_models(channel_name, task["traintuple_key"])
            head_model["traintuple_key"] = task["traintuple_key"]
            trunk_model["traintuple_key"] = task["traintuple_key"]
            return [head_model, trunk_model]
        else:
            in_model = _get_traintuple_out_model(channel_name, task["traintuple_key"])
            return [in_model]
    elif task_category == TASK_CATEGORY_COMPOSITETRAINTUPLE:
        if task["in_head_model"] and task["in_trunk_model"]:
            return [task["in_head_model"], task["in_trunk_model"]]
        else:
            return []
    elif task_category == TASK_CATEGORY_AGGREGATETUPLE:
        return task["in_models"] or {}


def _get_traintuple_out_model(channel_name: str, traintuple_key: str) -> Dict:
    # TODO orchestrator: this needs to die too
    res = get_traintuple_out_model(channel_name, traintuple_key)
    res["traintuple_key"] = traintuple_key
    return res


def _find_training_step_tuple_from_key(channel_name, tuple_key):
    # TODO orchestrator: burn with fire
    """Get tuple type and tuple metadata from tuple key.
    Applies to traintuple, composite traintuple and aggregatetuple.
    """
    metadata = get_object_from_ledger(channel_name, tuple_key, "queryModelDetails")
    if metadata.get("aggregatetuple"):
        return TASK_CATEGORY_AGGREGATETUPLE, metadata["aggregatetuple"]
    if metadata.get("composite_traintuple"):
        return TASK_CATEGORY_COMPOSITETRAINTUPLE, metadata["composite_traintuple"]
    if metadata.get("traintuple"):
        return TASK_CATEGORY_TRAINTUPLE, metadata["traintuple"]
    raise Exception(f"Key {tuple_key}: no tuple found for training step: model: {metadata}")


def _download_algo(channel_name: str, task_category: str, algo_key: str) -> bytes:
    query_method_names_mapper = {
        TASK_CATEGORY_TRAINTUPLE: "queryAlgo",
        TASK_CATEGORY_COMPOSITETRAINTUPLE: "queryCompositeAlgo",
        TASK_CATEGORY_AGGREGATETUPLE: "queryAggregateAlgo",
    }

    if task_category not in query_method_names_mapper:
        raise Exception(f"Cannot find algo with key {algo_key}")
    method_name = query_method_names_mapper[task_category]

    metadata = get_object_from_ledger(channel_name, algo_key, method_name)

    content = get_asset_content(
        channel_name,
        metadata["content"]["storage_address"],
        metadata["owner"],
        metadata["content"]["checksum"],
    )
    return content


def _download_objective(channel_name: str, objective_key: str) -> bytes:
    objective_metadata = get_object_from_ledger(channel_name, objective_key, "queryObjective")

    objective_content = get_asset_content(
        channel_name,
        objective_metadata["metrics"]["storage_address"],
        objective_metadata["owner"],
        objective_metadata["metrics"]["checksum"],
    )

    return objective_content


def _log_added(path: str) -> None:
    logger.debug(f"Added to buffer: {path}")

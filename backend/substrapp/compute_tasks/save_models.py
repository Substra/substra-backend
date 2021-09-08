import logging
import os
from django.conf import settings
from typing import Any, Tuple
from substrapp.utils import timeit
from django.urls import reverse
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.asset_buffer import add_model_from_path
from substrapp.compute_tasks.context import Context
from substrapp.utils import get_hash
import substrapp.orchestrator.computetask_pb2 as computetask_pb2
import substrapp.orchestrator.model_pb2 as model_pb2
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.orchestrator.api import get_orchestrator_client

logger = logging.getLogger(__name__)


def save_models(ctx: Context) -> object:

    task_category = ctx.task_category
    dirs = ctx.directories
    task_key = ctx.task_key

    if task_category in [computetask_pb2.TASK_TRAIN, computetask_pb2.TASK_AGGREGATE]:

        model_path = os.path.join(dirs.task_dir, TaskDirName.OutModels, Filenames.OutModel)
        model, storage_address = _save_model(ctx.channel_name, model_pb2.MODEL_SIMPLE, model_path, task_key)

        add_model_from_path(model_path, str(model.key))

        return {
            "end_model_key": model.key,
            "end_model_checksum": model.checksum,
            "end_model_storage_address": storage_address,
        }

    elif task_category == computetask_pb2.TASK_COMPOSITE:

        head_model_path = os.path.join(dirs.task_dir, TaskDirName.OutModels, Filenames.OutHeadModel)
        trunk_model_path = os.path.join(dirs.task_dir, TaskDirName.OutModels, Filenames.OutTrunkModel)

        head_model, _ = _save_model(ctx.channel_name, model_pb2.MODEL_HEAD, head_model_path, task_key)
        trunk_model, trunk_storage_address = _save_model(
            ctx.channel_name, model_pb2.MODEL_SIMPLE, trunk_model_path, task_key
        )

        add_model_from_path(head_model_path, str(head_model.key))
        add_model_from_path(trunk_model_path, str(trunk_model.key))

        return {
            "end_head_model_key": str(head_model.key),
            "end_head_model_checksum": head_model.checksum,
            # head_model has no storage_address
            "end_trunk_model_key": str(trunk_model.key),
            "end_trunk_model_checksum": trunk_model.checksum,
            "end_trunk_model_storage_address": trunk_storage_address,
        }
    else:
        raise Exception(f"Cannot save models for task category {task_category}")


@timeit
def _save_model(channel_name: str, category: int, src_path: str, task_key: str) -> Tuple[Any, str]:
    from substrapp.models import Model

    checksum = get_hash(src_path, task_key)
    instance = Model.objects.create(checksum=checksum, validated=True)

    with open(src_path, "rb") as f:
        instance.file.save("model", f)
    current_site = getattr(settings, "DEFAULT_DOMAIN")
    storage_address = f'{current_site}{reverse("substrapp:model-file", args=[instance.key])}'

    try:
        with get_orchestrator_client(channel_name) as client:
            client.register_model(
                {
                    "key": str(instance.key),
                    "category": category,
                    "compute_task_key": task_key,
                    "address": {
                        "checksum": checksum,
                        "storage_address": storage_address,
                    },
                }
            )
    except Exception as e:
        instance.delete()
        raise e

    return instance, storage_address

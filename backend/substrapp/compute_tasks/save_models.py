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
from substrapp.compute_tasks.categories import (
    TASK_CATEGORY_TRAINTUPLE,
    TASK_CATEGORY_AGGREGATETUPLE,
    TASK_CATEGORY_COMPOSITETRAINTUPLE,
)
from substrapp.compute_tasks.directories import TaskDirName

logger = logging.getLogger(__name__)


def save_models(ctx: Context) -> object:

    task_category = ctx.task_category
    dirs = ctx.directories
    task_key = ctx.task_key

    if task_category in [TASK_CATEGORY_TRAINTUPLE, TASK_CATEGORY_AGGREGATETUPLE]:

        model_path = os.path.join(dirs.task_dir, TaskDirName.OutModels, Filenames.OutModel)
        model, storage_address = _save_model(model_path, task_key)

        add_model_from_path(model_path, str(model.key))

        return {
            "end_model_key": model.key,
            "end_model_checksum": model.checksum,
            "end_model_storage_address": storage_address,
        }

    elif task_category == TASK_CATEGORY_COMPOSITETRAINTUPLE:

        head_model_path = os.path.join(dirs.task_dir, TaskDirName.OutModels, Filenames.OutHeadModel)
        trunk_model_path = os.path.join(dirs.task_dir, TaskDirName.OutModels, Filenames.OutTrunkModel)

        head_model, _ = _save_model(head_model_path, task_key)
        trunk_model, trunk_storage_address = _save_model(trunk_model_path, task_key)

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
def _save_model(src, task_key) -> Tuple[Any, str]:
    from substrapp.models import Model

    checksum = get_hash(src, task_key)
    instance = Model.objects.create(checksum=checksum, validated=True)

    with open(src, "rb") as f:
        instance.file.save("model", f)
    current_site = getattr(settings, "DEFAULT_DOMAIN")
    storage_address = f'{current_site}{reverse("substrapp:model-file", args=[instance.key])}'

    return instance, storage_address

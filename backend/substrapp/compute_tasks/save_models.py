import os
from uuid import UUID

import structlog
from django.conf import settings
from django.urls import reverse

import orchestrator
import orchestrator.model_pb2 as model_pb2
from api.errors import AlreadyExistsError
from api.serializers import ModelSerializer as ModelRepSerializer
from substrapp.compute_tasks.asset_buffer import add_model_from_path
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import get_hash
from substrapp.utils import timeit

logger = structlog.get_logger(__name__)


class SaveModelsError(Exception):
    """An error occurred while saving models"""


def save_models(ctx: Context) -> None:
    """Saves models produced by the task to the orchestrator and data storage

    Args:
        ctx (Context): the compute task context

    Raises:
        SaveModelsError: Raised if we can't save a model for this task kind
    """

    task_category = ctx.task.category
    dirs = ctx.directories
    task_key = ctx.task.key
    models = []

    if task_category not in [
        orchestrator.ComputeTaskCategory.TASK_AGGREGATE,
        orchestrator.ComputeTaskCategory.TASK_TRAIN,
        orchestrator.ComputeTaskCategory.TASK_COMPOSITE,
        orchestrator.ComputeTaskCategory.TASK_PREDICT,
    ]:
        raise SaveModelsError(f"Cannot save models for task category {task_category}")

    model_path = os.path.join(dirs.task_dir, TaskDirName.OutModels, Filenames.OutModel)
    output_identifier = ctx.get_output_identifier(model_path)
    simple_model = _save_model_to_local_storage(model_pb2.MODEL_SIMPLE, model_path, task_key, output_identifier)
    models.append(simple_model)

    if task_category == orchestrator.ComputeTaskCategory.TASK_COMPOSITE:
        # If we have a composite task we have two outputs, a MODEL_HEAD and a MODEL_SIMPLE model
        # so we need to register the head part separately
        head_model_path = os.path.join(dirs.task_dir, TaskDirName.OutModels, Filenames.OutHeadModel)
        output_identifier = ctx.get_output_identifier(head_model_path)
        head_model = _save_model_to_local_storage(model_pb2.MODEL_HEAD, head_model_path, task_key, output_identifier)
        models.append(head_model)

    try:
        with get_orchestrator_client(ctx.channel_name) as client:
            api_data_models = client.register_models({"models": models})
    except Exception as exc:
        for model in models:
            _delete_model(model["key"])
        raise exc

    for api_data in api_data_models:
        api_data["channel"] = ctx.channel_name
        api_serializer = ModelRepSerializer(data=api_data)
        try:
            api_serializer.save_if_not_exists()
        except AlreadyExistsError:
            pass

    add_model_from_path(model_path, str(simple_model["key"]))
    if task_category == orchestrator.ComputeTaskCategory.TASK_COMPOSITE:
        add_model_from_path(head_model_path, str(head_model["key"]))


@timeit
def _save_model_to_local_storage(category: int, src_path: str, task_key: str, task_output_identifier: str) -> UUID:
    """Saves a model to the orchestrator and in the data storage

    Args:
        category (int): model category (head, simple)
        src_path (str): path of the model file on the filesystem
        task_key (str): key of the task that created the model

    Returns:
        UUID: the model key
    """
    from substrapp.models import Model

    checksum = get_hash(src_path, task_key)
    instance = Model.objects.create(checksum=checksum)

    with open(src_path, "rb") as f:
        instance.file.save("model", f)
    current_site = settings.DEFAULT_DOMAIN
    storage_address = f'{current_site}{reverse("api:model-file", args=[instance.key])}'

    logger.debug("Saving model in local storage", model_key=instance.key, model_category=category)

    return {
        "key": str(instance.key),
        "category": category,
        "compute_task_key": task_key,
        "compute_task_output_identifier": task_output_identifier,
        "address": {
            "checksum": checksum,
            "storage_address": storage_address,
        },
    }


def _delete_model(model_key: str) -> None:
    """Deletes a model from the local storage

    Args:
        model_key (str): key of the model you want to delete
    """
    from substrapp.models import Model

    Model.objects.get(key=model_key).delete()

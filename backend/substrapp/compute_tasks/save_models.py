from uuid import UUID

import structlog
from django.conf import settings
from django.urls import reverse

from substrapp.utils import get_hash
from substrapp.utils import timeit

logger = structlog.get_logger(__name__)


class SaveModelsError(Exception):
    """An error occurred while saving models"""


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
    storage_address = f'{current_site}{reverse("localrep:model-file", args=[instance.key])}'

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

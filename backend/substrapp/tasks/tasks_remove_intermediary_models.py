import logging
from typing import List
from backend.celery import app
from substrapp.orchestrator import get_orchestrator_client
from substrapp.compute_tasks.asset_buffer import delete_models_from_buffer

logger = logging.getLogger(__name__)


@app.task(ignore_result=False)
def remove_intermediary_models(channel_name: str, model_keys: List[str]) -> None:
    from substrapp.models import Model

    models = Model.objects.filter(key__in=model_keys, validated=True)
    filtered_model_keys = [str(model.key) for model in models]

    # TODO horizontal scaling: this deletion needs to happen on the backend, so that we can stop mounting
    # the volume in write-mode on the worker. This also depends on the choice of data implementation (i.e. minio?)
    models.delete()

    delete_models_from_buffer(model_keys)  # TODO horizontal scaling: this need to run on every worker?

    if filtered_model_keys:

        with get_orchestrator_client(channel_name) as client:
            for model_key in filtered_model_keys:
                client.disable_model(model_key)

        log_model_keys = ", ".join(filtered_model_keys)
        logger.info(f"Delete intermediary models: {log_model_keys}")


@app.task(ignore_result=False)
def remove_intermediary_models_from_buffer(model_key: str) -> None:
    delete_models_from_buffer([model_key])

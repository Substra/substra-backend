import json
import os

import structlog
from django.conf import settings
from django.urls import reverse

import orchestrator
import orchestrator.model_pb2 as model_pb2
from localrep.errors import AlreadyExistsError
from localrep.serializers import ModelSerializer as ModelRepSerializer
from orchestrator.client import OrchestratorClient
from substrapp.compute_tasks import context
from substrapp.compute_tasks import directories
from substrapp.compute_tasks.asset_buffer import add_model_from_path
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import get_hash

logger = structlog.get_logger(__name__)

# Temporarily determine model category based on output identifier
OUTPUT_HEAD_MODEL_IDENTIFIERS = ["local", "head"]


class OutputSaver:
    def __init__(self, ctx: context.Context):
        self._ctx = ctx

    def save_outputs(self) -> None:
        """Saves the task outputs"""
        performances = [o for o in self._ctx.outputs if o.kind == orchestrator.AssetKind.ASSET_PERFORMANCE]
        models = [o for o in self._ctx.outputs if o.kind == orchestrator.AssetKind.ASSET_MODEL]

        for perf in performances:
            self._save_performance(perf)

        if models:
            self._save_models(models)

        if self._ctx.has_chainkeys:
            directories.commit_dir(
                self._ctx.directories, directories.TaskDirName.Chainkeys, directories.CPDirName.Chainkeys
            )

    def _save_performance(self, output: context.OutputResource):
        logger.info("saving performances")
        with get_orchestrator_client(self._ctx.channel_name) as client:
            perf_path = os.path.join(self._ctx.directories.task_dir, output.rel_path)
            perf = _get_perf(perf_path)
            _register_perf(client, self._ctx.task.key, self._ctx.algo.key, perf, output.identifier)

    def _save_models(self, models: list[context.OutputResource]):
        logger.info("saving models")

        local_models = []
        for model in models:
            local_model = self._save_model_to_local_storage(model)
            local_models.append(local_model)

        try:
            with get_orchestrator_client(self._ctx.channel_name) as client:
                localrep_data_models = client.register_models({"models": local_models})
        except Exception as exc:
            for model in local_models:
                self._delete_model(model["key"])
            raise exc

        for localrep_data in localrep_data_models:
            localrep_data["channel"] = self._ctx.channel_name
            localrep_serializer = ModelRepSerializer(data=localrep_data)
            try:
                localrep_serializer.save_if_not_exists()
            except AlreadyExistsError:
                pass

        for model, local in zip(models, local_models):
            path = os.path.join(self._ctx.directories.task_dir, model.rel_path)
            add_model_from_path(path, local["key"])

    def _save_model_to_local_storage(self, model: context.OutputResource) -> dict:
        path = os.path.join(self._ctx.directories.task_dir, model.rel_path)
        from substrapp.models import Model

        checksum = get_hash(path, self._ctx.task.key)
        instance = Model.objects.create(checksum=checksum)

        with open(path, "rb") as f:
            instance.file.save("model", f)
        current_site = settings.DEFAULT_DOMAIN
        storage_address = f'{current_site}{reverse("substrapp:model-file", args=[instance.key])}'

        logger.debug("Saving model in local storage", model_key=instance.key, identifier=model.identifier)

        return {
            "key": str(instance.key),
            "compute_task_key": self._ctx.task.key,
            "compute_task_output_identifier": model.identifier,
            "category": _get_model_category(model.identifier),
            "address": {
                "checksum": checksum,
                "storage_address": storage_address,
            },
        }

    def _delete_model(self, key: str):
        """Delete model from local storage in case something went wrong during registration"""
        from substrapp.models import Model

        Model.objects.get(key=key).delete()


def _register_perf(client: OrchestratorClient, task_key: str, algo_key: str, perf: float, identifier: str) -> None:
    """Registers the performance on the orchestrator

    Args:
        client: An open orchestrator client.
        task_key: The key of the compute task that produced this performances.
        algo_key: The key of the algo that produced this performance.
        perf: The performance value.
    """
    performance_obj = {
        "compute_task_key": task_key,
        "metric_key": algo_key,
        "performance_value": perf,
        "compute_task_output_identifier": identifier,
    }
    client.register_performance(performance_obj)


def _get_perf(perf_path: str) -> float:
    """Retrieves the performance from the performance file produced by the task

    Args:
        dirs: The compute task directories that contains the task outputs.
        metric_key: The key of the metric from which we want to retrieve the performance.

    Returns:
        The performance as a floating point value.
    """
    with open(perf_path, "r") as perf_file:
        perf = json.load(perf_file)["all"]
        return float(perf)


def _get_model_category(identifier: str) -> str:
    """Temporarily hardcode a match between model identifier and category.

    This is based on the following assumptions and should be removed once we drop model categories:
    - all models are SIMPLE
    - except "local" or "head" outputs
    """

    return model_pb2.MODEL_HEAD if identifier.lower() in OUTPUT_HEAD_MODEL_IDENTIFIERS else model_pb2.MODEL_SIMPLE

from __future__ import absolute_import, unicode_literals
import logging
from django.conf import settings
from backend.celery import app
from substrapp.compute_tasks.asset_buffer import delete_models_from_buffer
from substrapp.compute_tasks.context import get_algo_image_tag
from substrapp.compute_tasks.directories import Directories, teardown_compute_plan_dir
from substrapp.compute_tasks.compute_pod import delete_compute_plan_pods
from substrapp.docker_registry import delete_container_image

logger = logging.getLogger(__name__)


@app.task(ignore_result=False)
def on_compute_plan(channel_name, compute_plan):

    compute_plan_key = compute_plan["compute_plan_key"]
    algo_keys = compute_plan["algo_keys"]
    model_keys = compute_plan["models_to_delete"]
    status = compute_plan["status"]

    if status in ["done", "failed", "canceled"]:

        if not settings.DEBUG_KEEP_POD_AND_DIRS:
            delete_compute_plan_pods(compute_plan_key)
            dirs = Directories(compute_plan_key)
            teardown_compute_plan_dir(dirs)

        if not settings.DEBUG_QUICK_IMAGE:
            _remove_algo_images(algo_keys)

    if model_keys:
        _remove_intermediary_models(model_keys)


def _remove_intermediary_models(model_keys):
    from substrapp.models import Model

    models = Model.objects.filter(key__in=model_keys, validated=True)
    filtered_model_keys = [str(model.key) for model in models]

    # TODO horizontal scaling: this deletion needs to happen on the backend, so that we can stop mounting
    # the volume in write-mode on the worker. This also depends on the choice of data implementation (i.e. minio?)
    models.delete()

    delete_models_from_buffer(model_keys)  # TODO horizontal scaling: this need to run on every worker?

    if filtered_model_keys:
        log_model_keys = ", ".join(filtered_model_keys)
        logger.info(f"Delete intermediary models: {log_model_keys}")


def _remove_algo_images(algo_keys):
    for algo_key in algo_keys:
        image_tag = get_algo_image_tag(algo_key)
        delete_container_image(image_tag)

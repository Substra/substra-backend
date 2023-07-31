import structlog
from django.conf import settings

import orchestrator
from backend.celery import app
from builder.exceptions import BuildRetryError
from builder.exceptions import CeleryNoRetryError
from builder.image_builder.image_builder import build_image_if_missing
from builder.tasks.task import BuildTask

logger = structlog.get_logger(__name__)
max_retries = settings.CELERY_TASK_MAX_RETRIES


@app.task(
    bind=True,
    base=BuildTask,
)
# Ack late and reject on worker lost allows use to
# see http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-reject-on-worker-lost
# and https://github.com/celery/celery/issues/5106
def build_image(task: BuildTask, function_serialized: str, channel_name: str) -> None:
    function = orchestrator.Function.parse_raw(function_serialized)

    attempt = 0
    while attempt <= task.max_retries:
        try:
            # TODO refactor
            build_image_if_missing(channel_name, function)
        except BuildRetryError as e:
            logger.info(
                "Retrying build",
                function_id=function.key,
                attempt=(task.attempt + 1),
                max_attempts=(task.max_retries + 1),
            )
            attempt += 1
            if attempt >= task.max_retries:
                logger.exception(e)
                raise CeleryNoRetryError from e
            else:
                continue
        break

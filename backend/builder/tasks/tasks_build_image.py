import orchestrator
from backend.celery import app
from builder.image_builder.image_builder import build_image_if_missing


@app.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=False,
)
# Ack late and reject on worker lost allows use to
# see http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-reject-on-worker-lost
# and https://github.com/celery/celery/issues/5106
def build_image(self, function_serialized: str, channel: str):
    function = orchestrator.Function.parse_raw(function_serialized)
    build_image_if_missing(channel, function)

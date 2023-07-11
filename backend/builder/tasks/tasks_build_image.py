import orchestrator
from backend.celery import app


@app.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=False,
)
# Ack late and reject on worker lost allows use to
# see http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-reject-on-worker-lost
# and https://github.com/celery/celery/issues/5106
def build_image(function_serialized: str):
    function = orchestrator.Function.parse_raw(function_serialized)
    print(f"youpi!!!! {function.key}")

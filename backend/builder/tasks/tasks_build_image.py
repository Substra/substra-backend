import orchestrator
from backend.celery import app
from builder.image_builder.image_builder import build_image_if_missing
from builder.tasks.task import BuildTask
from substrapp.models.compute_task_profiling import ComputeTaskSteps
from substrapp.tasks.tasks_task_profiling import create_task_profiling_step
from substrapp.utils import Timer


@app.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=False,
    base=BuildTask,
)
# Ack late and reject on worker lost allows use to
# see http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-reject-on-worker-lost
# and https://github.com/celery/celery/issues/5106
def build_image(task: BuildTask, function_serialized: str, channel: str, compute_task_key: str) -> None:
    function = orchestrator.Function.parse_raw(function_serialized)

    timer = Timer()
    timer.start()
    build_image_if_missing(channel, function)

    create_task_profiling_step.apply_async((channel, compute_task_key, ComputeTaskSteps.BUILD_IMAGE, str(timer.stop())))

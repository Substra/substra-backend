from backend.celery import app
from substrapp.docker_registry import run_garbage_collector


@app.task(ignore_result=True)
def docker_registry_garbage_collector_task() -> None:
    run_garbage_collector()

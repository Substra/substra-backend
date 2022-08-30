from backend.celery import app
from substrapp.docker_registry import delete_container_image_safe
from substrapp.docker_registry import fetch_old_algo_image_names
from substrapp.docker_registry import run_garbage_collector


@app.task(ignore_result=True)
def clean_old_images_task(max_duration: int) -> None:
    algo_image_names = fetch_old_algo_image_names(max_duration)
    for algo_image_name in algo_image_names:
        delete_container_image_safe(algo_image_name)


@app.task(ignore_result=True)
def docker_registry_garbage_collector_task() -> None:
    run_garbage_collector()

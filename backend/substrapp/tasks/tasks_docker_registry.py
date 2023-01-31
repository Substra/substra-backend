from backend.celery import app
from substrapp.docker_registry import delete_container_image_safe
from substrapp.docker_registry import fetch_old_function_image_names
from substrapp.docker_registry import run_garbage_collector


@app.task(ignore_result=True)
def clean_old_images_task(max_duration: int) -> None:
    function_image_names = fetch_old_function_image_names(max_duration)
    for function_image_name in function_image_names:
        delete_container_image_safe(function_image_name)


@app.task(ignore_result=True)
def docker_registry_garbage_collector_task() -> None:
    run_garbage_collector()

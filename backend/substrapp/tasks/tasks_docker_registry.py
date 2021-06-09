from backend.celery import app
from substrapp.docker_registry import fetch_old_algo_image_names, run_garbage_collector, delete_container_image


@app.task(ignore_result=True)
def clean_old_images_task(max_duration):
    algo_image_names = fetch_old_algo_image_names(max_duration)
    for algo_image_name in algo_image_names:
        delete_container_image(algo_image_name)


@app.task(ignore_result=True)
def docker_registry_garbage_collector_task():
    run_garbage_collector()

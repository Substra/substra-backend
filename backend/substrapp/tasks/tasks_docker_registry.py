from backend.celery import app
from substrapp.docker_registry import delete_container_image
from substrapp.docker_registry import fetch_old_algo_image_names
from substrapp.docker_registry import run_garbage_collector
from substrapp.models.image_entrypoint import ImageEntrypoint


@app.task(ignore_result=True)
def clean_old_images_task(max_duration):
    algo_image_names = fetch_old_algo_image_names(max_duration)
    for algo_image_name in algo_image_names:
        delete_container_image(algo_image_name)
        ImageEntrypoint.objects.filter(asset_key=algo_image_name).delete()


@app.task(ignore_result=True)
def docker_registry_garbage_collector_task():
    run_garbage_collector()

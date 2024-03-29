import structlog

from backend.celery import app
from substrapp.compute_tasks.asset_buffer import delete_models_from_buffer
from substrapp.compute_tasks.datastore import Datastore
from substrapp.compute_tasks.datastore import DatastoreError
from substrapp.compute_tasks.datastore import get_datastore

logger = structlog.get_logger(__name__)


def queue_remove_intermediary_models_from_buffer(model_key: str) -> None:
    # This task is broadcast to all worker (see the broadcast defined in backend/celery.py)
    remove_intermediary_models_from_buffer.apply_async((model_key,))


# This task is routed to run on the broadcast exchange
# Each worker is listening to the broadcast queue. All running worker will perform this task.
# Multiple tasks with the same task_id are created in the db
# With ignore_result set to true, we ignore the result of the task as the different task state
# result might be conflicting.
# See https://docs.celeryproject.org/en/stable/userguide/routing.html#Broadcast&Results
@app.task(ignore_result=True)
def remove_intermediary_models_from_buffer(model_key: str) -> None:
    delete_models_from_buffer([model_key])


def queue_remove_intermediary_model_from_db(channel_name: str, model_key: str) -> None:
    from substrapp.task_routing import get_generic_worker_queue

    worker_queue = get_generic_worker_queue()

    remove_intermediary_model_from_db.apply_async((channel_name, model_key), queue=worker_queue)


@app.task(ignore_result=False)
def remove_intermediary_model_from_db(channel_name: str, model_key: str) -> None:
    datastore = get_datastore(channel_name)
    _delete_intermediary_model_from_db(datastore, model_key)


def _delete_intermediary_model_from_db(datastore: Datastore, model_key: str) -> None:
    try:
        datastore.delete_model(model_key)
    except DatastoreError:
        logger.debug("model deletion from datastore failed", model_key=model_key)

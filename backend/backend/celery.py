import logging
import os

from celery import Celery
from celery import current_app
from celery.signals import after_task_publish
from celery.signals import celeryd_init
from celery.signals import setup_logging
from django_structlog.celery.steps import DjangoStructLogInitStep
from kombu.common import Broadcast

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.prod")

from django.conf import settings  # noqa: E402

app = Celery("backend")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.steps["worker"].add(DjangoStructLogInitStep)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


# Declare broadcasting queue across worker
app.conf.task_queues = (Broadcast(settings.CELERY_BROADCAST),)

app.conf.task_routes = {
    "substrapp.tasks.tasks_remove_intermediary_models.remove_intermediary_models_from_buffer": {
        "queue": settings.CELERY_BROADCAST,
        "exchange": settings.CELERY_BROADCAST,
    }
}


@celeryd_init.connect
def setup_log_format(sender, conf, **kwargs):
    conf.worker_log_format = """
        %(asctime)s: %(levelname)s/%(processName)s {0} %(message)s
    """.strip().format(
        sender
    )
    conf.worker_task_log_format = (
        "%(asctime)s: %(levelname)s/%(processName)s {0} " "[%(task_name)s(%(task_id)s)] %(message)s"
    ).format(sender)


@setup_logging.connect
def receiver_setup_logging(loglevel, logfile, format, colorize, **kwargs):  # pragma: no cover
    """setup structlog for celery
    See https://django-structlog.readthedocs.io/en/latest/celery.html#configure-celery-s-logger
    """
    logging.config.dictConfig(settings.LOGGING)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from substrapp.tasks.tasks_docker_registry import clean_old_images_task
    from substrapp.tasks.tasks_docker_registry import docker_registry_garbage_collector_task
    from users.tasks import flush_expired_tokens

    period = int(settings.CELERYBEAT_FLUSH_EXPIRED_TOKENS_TASK_PERIOD)
    sender.add_periodic_task(period, flush_expired_tokens.s(), queue="scheduler", name="flush expired tokens")

    # Launch docker-registry garbage-collector to really remove images
    sender.add_periodic_task(
        1800, docker_registry_garbage_collector_task.s(), queue="scheduler", name="garbage collect docker registry"
    )

    max_images_ttl = int(settings.CELERYBEAT_MAXIMUM_IMAGES_TTL)
    sender.add_periodic_task(
        3600,
        clean_old_images_task.s(),
        queue="scheduler",
        args=[max_images_ttl],
        name="remove old images from docker registry",
    )


@after_task_publish.connect
def update_task_state(sender=None, headers=None, body=None, **kwargs):
    # Change task.status to 'WAITING' for all tasks which are sent in.
    # This allows one to distinguish between PENDING tasks which have been
    # sent in and tasks which do not exist. State will change to
    # SUCCESS, FAILURE, etc. once the process terminates.
    task = current_app.tasks.get(sender)
    backend = task.backend if task else current_app.backend
    backend.store_result(headers["id"], None, "WAITING")

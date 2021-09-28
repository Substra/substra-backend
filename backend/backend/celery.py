from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery
from celery import current_app
from celery.signals import after_task_publish, celeryd_init, setup_logging
from django_structlog.celery.steps import DjangoStructLogInitStep

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.prod')

from django.conf import settings

app = Celery('backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.steps['worker'].add(DjangoStructLogInitStep)


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@celeryd_init.connect
def setup_log_format(sender, conf, **kwargs):
    conf.worker_log_format = """
        %(asctime)s: %(levelname)s/%(processName)s {0} %(message)s
    """.strip().format(sender)
    conf.worker_task_log_format = (
        '%(asctime)s: %(levelname)s/%(processName)s {0} '
        '[%(task_name)s(%(task_id)s)] %(message)s'
    ).format(sender)


@setup_logging.connect
def receiver_setup_logging(loglevel, logfile, format, colorize, **kwargs):  # pragma: no cover
    """setup structlog for celery
    See https://django-structlog.readthedocs.io/en/latest/celery.html#configure-celery-s-logger
    """
    logging.config.dictConfig(settings.LOGGING)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from substrapp.tasks.tasks_prepare_task import prepare_training_task
    from substrapp.tasks.tasks_prepare_task import prepare_testing_task
    from substrapp.tasks.tasks_prepare_task import prepare_aggregate_task
    from substrapp.tasks.tasks_prepare_task import prepare_composite_training_task
    from substrapp.tasks.tasks_docker_registry import docker_registry_garbage_collector_task
    from substrapp.tasks.tasks_docker_registry import clean_old_images_task

    period = int(os.environ.get('SCHEDULE_TASK_PERIOD', 3 * 3600))

    for channel_name in settings.LEDGER_CHANNELS.keys():
        sender.add_periodic_task(period, prepare_training_task.s(), queue='scheduler', args=[channel_name],
                                 name='query Traintuples to prepare train task on todo traintuples')
        sender.add_periodic_task(period, prepare_testing_task.s(), queue='scheduler', args=[channel_name],
                                 name='query Testuples to prepare test task on todo testuples')
        sender.add_periodic_task(period, prepare_aggregate_task.s(), queue='scheduler', args=[channel_name],
                                 name='query Aggregatetuples to prepare task on todo aggregatetuples')
        sender.add_periodic_task(period, prepare_composite_training_task.s(), queue='scheduler', args=[channel_name],
                                 name='query CompositeTraintuples to prepare task on todo composite_traintuples')

    from users.tasks import flush_expired_tokens

    period = int(os.environ.get('FLUSH_EXPIRED_TOKENS_TASK_PERIOD', 24 * 3600))
    sender.add_periodic_task(period, flush_expired_tokens.s(), queue='scheduler',
                             name='flush expired tokens')

    # Launch docker-registry garbage-collector to really remove images
    sender.add_periodic_task(1800, docker_registry_garbage_collector_task.s(), queue='scheduler',
                             name='garbage collect docker registry')

    max_images_ttl = int(os.environ.get('MAXIMUM_IMAGES_TTL', 7 * 24 * 3600))
    sender.add_periodic_task(3600, clean_old_images_task.s(), queue='scheduler', args=[max_images_ttl],
                             name='remove old images from docker registry')


@after_task_publish.connect
def update_task_state(sender=None, headers=None, body=None, **kwargs):
    # Change task.status to 'WAITING' for all tasks which are sent in.
    # This allows one to distinguish between PENDING tasks which have been
    # sent in and tasks which do not exist. State will change to
    # SUCCESS, FAILURE, etc. once the process terminates.
    task = current_app.tasks.get(sender)
    backend = task.backend if task else current_app.backend
    backend.store_result(headers['id'], None, 'WAITING')

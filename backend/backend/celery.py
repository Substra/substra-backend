from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery import current_app
from celery.signals import after_task_publish, celeryd_init

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.prod')

from django.conf import settings

app = Celery('backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

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


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from substrapp.tasks.tasks import (prepare_training_task,
                                       prepare_testing_task,
                                       prepare_aggregate_task,
                                       prepare_composite_training_task)

    period = int(os.environ.get('SCHEDULE_TASK_PERIOD', 3 * 3600))

    for channel_name in settings.LEDGER_CHANNELS:
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


@after_task_publish.connect
def update_task_state(sender=None, headers=None, body=None, **kwargs):
    # Change task.status to 'WAITING' for all tasks which are sent in.
    # This allows one to distinguish between PENDING tasks which have been
    # sent in and tasks which do not exist. State will change to
    # SUCCESS, FAILURE, etc. once the process terminates.
    task = current_app.tasks.get(sender)
    backend = task.backend if task else current_app.backend
    backend.store_result(headers['id'], None, 'WAITING')

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'substrabac.settings.prod')

app = Celery('substrabac')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from substrapp.tasks.tasks import prepareTrainingTask, prepareTestingTask

    period = 3 * 3600
    sender.add_periodic_task(period, prepareTrainingTask.s(), queue='scheduler',
                             name='query Traintuples to prepare train task on todo traintuples')
    sender.add_periodic_task(period, prepareTestingTask.s(), queue='scheduler',
                             name='query Testuples to prepare test task on todo testuples')

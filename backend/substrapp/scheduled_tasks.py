import os
from django.conf import settings


def setup_scheduled_tasks(sender):
    from substrapp.tasks.tasks_prepare_task import (
        prepare_training_task,
        prepare_testing_task,
        prepare_aggregate_task,
        prepare_composite_training_task,
    )
    from substrapp.tasks.tasks_docker_registry import docker_registry_garbage_collector_task, clean_old_images_task
    from users.tasks import flush_expired_tokens

    period = int(os.environ.get("SCHEDULE_TASK_PERIOD", 3 * 3600))

    for channel_name in settings.LEDGER_CHANNELS.keys():
        sender.add_periodic_task(
            period,
            prepare_training_task.s(),
            queue="scheduler",
            args=[channel_name],
            name="query Traintuples to prepare train task on todo traintuples",
        )
        sender.add_periodic_task(
            period,
            prepare_testing_task.s(),
            queue="scheduler",
            args=[channel_name],
            name="query Testuples to prepare test task on todo testuples",
        )
        sender.add_periodic_task(
            period,
            prepare_aggregate_task.s(),
            queue="scheduler",
            args=[channel_name],
            name="query Aggregatetuples to prepare task on todo aggregatetuples",
        )
        sender.add_periodic_task(
            period,
            prepare_composite_training_task.s(),
            queue="scheduler",
            args=[channel_name],
            name="query CompositeTraintuples to prepare task on todo composite_traintuples",
        )

    period = int(os.environ.get("FLUSH_EXPIRED_TOKENS_TASK_PERIOD", 24 * 3600))
    sender.add_periodic_task(period, flush_expired_tokens.s(), queue="scheduler", name="flush expired tokens")

    # Launch docker-registry garbage-collector to really remove images
    sender.add_periodic_task(
        1800, docker_registry_garbage_collector_task.s(), queue="scheduler", name="garbage collect docker registry"
    )

    max_images_ttl = int(os.environ.get("MAXIMUM_IMAGES_TTL", 7 * 24 * 3600))
    sender.add_periodic_task(
        3600,
        clean_old_images_task.s(),
        queue="scheduler",
        args=[max_images_ttl],
        name="remove old images from docker registry",
    )

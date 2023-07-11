from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from substrapp.kubernetes_utils import get_worker_replica_set_scale
from substrapp.models.computeplan_worker_mapping import ComputePlanWorkerMapping

"""
Mapping compute plans to workers makes sure that the tasks that have to be executed by
/ on a compute pod are always sent to the worker on which the compute pod is.
This is necessary for compute tasks and for compute pod removal.

The ComputePlanWorkerMapping psql table records which compute plan is mapped to which
worker.
For traceability reasons, the "release_date" column keeps history on
computeplan/worker mapping.
- "release_date" with DateTime value: there was a compute pod for this compute plan on
this worker, but there is not anymore. The date gives the datetime when the worker was
released.
- empty "release_date" means: there is __currently__ a compute pod for this compute plan
on this worker.

At a given point in time, a compute plan can only be mapped to one worker. This is
enforced by a unique condition in the ComputePlanWorkerMapping model.
"""


WORKER_QUEUE = f"{settings.ORG_NAME}.worker"
BUILDER_QUEUE = f"{settings.ORG_NAME}.builder"


def get_generic_worker_queue() -> str:
    """Return the name of a queue which all the workers listen to"""
    return WORKER_QUEUE


def get_worker_queue(compute_plan_key: str) -> str:
    """
    Return a worker queue for a compute plan key.

    If no no mapping between this compute plan and a worker exists, such mapping is created
    """
    worker_index = _acquire_worker_index(compute_plan_key)
    return _get_worker_queue(worker_index)


def get_builder_queue() -> str:
    return BUILDER_QUEUE


def get_existing_worker_queue(compute_plan_key: str) -> Optional[str]:
    """
    Return the name of a worker queue mapped to this compute plan, if it exists.

    If it doesn't exist, return None
    """
    mappings = list(
        ComputePlanWorkerMapping.objects.filter(
            compute_plan_key=compute_plan_key,
            release_date=None,
        )
    )
    return _get_worker_queue(mappings[0].worker_index) if mappings else None


@transaction.atomic
def release_worker(compute_plan_key: str) -> None:
    """Add the release date to the mapping between this compute plan and a worker"""
    from substrapp.models.computeplan_worker_mapping import ComputePlanWorkerMapping

    try:
        mapping = ComputePlanWorkerMapping.objects.get(
            compute_plan_key=compute_plan_key,
            release_date=None,
        )
    except ComputePlanWorkerMapping.DoesNotExist:  # worker was already released by a concurrent process
        return

    mapping.release_date = timezone.now()
    mapping.save()


@transaction.atomic
def _acquire_worker_index(compute_plan_key: str) -> int:
    mapping = list(
        ComputePlanWorkerMapping.objects.filter(
            compute_plan_key=compute_plan_key,
            release_date=None,
        )
    )

    # if a mapping exists, return the corresponding worker index
    if mapping:
        return mapping[0].worker_index

    eligible_workers_indexes = _get_workers_with_fewest_running_cps()

    # Get the first worker with the least running cps
    worker_index = sorted(eligible_workers_indexes)[0]

    # save into the mapping the selected worker
    ComputePlanWorkerMapping(compute_plan_key=compute_plan_key, worker_index=worker_index).save()

    return worker_index


def _get_workers_with_fewest_running_cps() -> list[int]:
    """
    Return the list of worker indexes with the fewest running Compute Plans.

    For instance:

    - If no CP is running, then return the list of all the worker indexes.
    - If every worker has a running CP except worker of index A, then return the list [A].
    - If there are 3 workers of index A, B, and C, and workers A and B have 2 running CPs, and worker C has 1 running
      CP, then return the list [C]
    """
    cp_count_per_worker = (
        ComputePlanWorkerMapping.objects.filter(release_date=None)
        .values("worker_index")
        .annotate(cp_count=Count("compute_plan_key"))
    )

    num_workers = get_worker_replica_set_scale()
    count_by_idx = dict.fromkeys(range(num_workers), 0)

    for cp_per_worker in cp_count_per_worker:
        worker_index = cp_per_worker["worker_index"]
        cp_count = cp_per_worker["cp_count"]
        count_by_idx[worker_index] = cp_count

    min_count = min(count_by_idx.values())
    eligible = filter(lambda w_idx: count_by_idx[w_idx] == min_count, count_by_idx)

    return list(eligible)


def _get_worker_queue(worker_index: int) -> str:
    """Return the name of a queue which the worker identified by "worker_index" listens to"""
    return f"{WORKER_QUEUE}-{worker_index}"

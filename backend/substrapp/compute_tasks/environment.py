import os
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.transfer_bucket import (
    TAG_VALUE_FOR_TRANSFER_BUCKET,
    TRANSFER_BUCKET_TESTTUPLE_TAG,
)
import substrapp.orchestrator.computetask_pb2 as computetask_pb2


def get_environment(ctx: Context):
    env = {}

    # Node index
    node_index = os.getenv("NODE_INDEX")
    if node_index:
        env["NODE_INDEX"] = node_index

    # Transfer bucket
    tag = ctx.task.get("tag")
    if ctx.task_category == computetask_pb2.TASK_TEST:
        if tag and TAG_VALUE_FOR_TRANSFER_BUCKET in tag:
            env[TRANSFER_BUCKET_TESTTUPLE_TAG] = TAG_VALUE_FOR_TRANSFER_BUCKET

    return env

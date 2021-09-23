import os
from substrapp.compute_tasks.context import Context


def get_environment(ctx: Context):
    env = {}

    # Node index
    node_index = os.getenv("NODE_INDEX")
    if node_index:
        env["NODE_INDEX"] = node_index

    return env

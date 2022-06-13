import os
from typing import Dict

from substrapp.compute_tasks.context import Context


def get_environment(ctx: Context) -> Dict[str, str]:
    env = {}

    organization_index = os.getenv("ORGANIZATION_INDEX")
    if organization_index:
        env["ORGANIZATION_INDEX"] = organization_index

    return env

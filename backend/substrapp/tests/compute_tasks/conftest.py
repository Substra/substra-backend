import uuid
from typing import Any

import pytest

import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.compute_tasks.algo import Algo
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import Directories

DOCKERFILE = """
FROM ubuntu:16.04
RUN echo "Hello World"
ENTRYPOINT ["python3", "myalgo.py"]
"""


@pytest.fixture
def algo() -> Algo:
    channel = "mychannel"
    algo = {
        "key": "ae0fa090-7ba9-48b3-b6c9-fe0feef088ef",
        "name": "my algo",
        "category": 1,
        "owner": "Org1MSP",
        "description": {"checksum": "", "storage_address": ""},
        "algorithm": {"checksum": "", "storage_address": ""},
        "permissions": {
            "process": {"public": True, "authorized_ids": []},
            "download": {"public": True, "authorized_ids": []},
        },
    }
    return Algo(channel, algo)


@pytest.fixture
def orc_metric() -> dict[str, Any]:
    return {
        "key": "fca0f83f-381e-4a2a-ab54-d009fb00b4af",
        "name": "my metric",
        "category": 4,
        "owner": "Org1MSP",
        "description": {"checksum": "", "storage_address": ""},
        "algorithm": {"checksum": "", "storage_address": ""},
        "permissions": {
            "process": {"public": True, "authorized_ids": []},
            "download": {"public": True, "authorized_ids": []},
        },
    }


@pytest.fixture
def testtuple_context(orc_metric) -> Context:
    cp_key = str(uuid.uuid4())
    return Context(
        channel_name="mychannel",
        task={},
        task_category=computetask_pb2.TASK_TEST,
        task_key=str(uuid.uuid4()),
        compute_plan={},
        compute_plan_key=cp_key,
        compute_plan_tag="",
        in_models=[],
        algo={},
        metrics=[orc_metric],
        data_manager={"name": "test data_manager"},
        directories=Directories(cp_key),
        has_chainkeys=False,
    )

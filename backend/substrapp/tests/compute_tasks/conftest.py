import uuid
from typing import Any

import pytest

import orchestrator
import orchestrator.mock as orc_mock
from orchestrator.resources import AssetKind
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import Directories
from substrapp.tests.common import InputIdentifiers

DOCKERFILE = """
FROM ubuntu:16.04
RUN echo "Hello World"
ENTRYPOINT ["python3", "myalgo.py"]
"""


@pytest.fixture
def algo() -> orchestrator.Algo:
    return orc_mock.AlgoFactory()


@pytest.fixture
def orc_metric() -> dict[str, Any]:
    return {
        "key": "fca0f83f-381e-4a2a-ab54-d009fb00b4af",
        "name": "my metric",
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
        task_key=str(uuid.uuid4()),
        compute_plan={},
        compute_plan_key=cp_key,
        compute_plan_tag="",
        input_assets=[],
        algo=orc_metric,
        directories=Directories(cp_key),
        has_chainkeys=False,
    )


@pytest.fixture
def archived_datamanager_task_input_context():
    cp_key = str(uuid.uuid4())
    archived_dm = orc_mock.DataManagerFactory(archived=True)
    task_input = orc_mock.ComputeTaskInputAsset(
        identifier=InputIdentifiers.OPENER, kind=AssetKind.ASSET_DATA_MANAGER, data_manager=archived_dm
    )

    return Context(
        channel_name="mychannel",
        task=orc_mock.ComputeTaskFactory(),
        compute_plan={},
        input_assets=[task_input],
        algo=orc_mock.AlgoFactory(),
        directories=Directories(cp_key),
        has_chainkeys=False,
    )

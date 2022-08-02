import uuid

from google.protobuf.json_format import MessageToDict

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.common_pb2 as common_pb2
import orchestrator.computetask_pb2 as computetask_pb2
from orchestrator.client import CONVERT_SETTINGS
from substrapp.compute_tasks import algo
from substrapp.compute_tasks import context
from substrapp.tests.common import InputIdentifiers
from substrapp.tests.orchestrator_factory import Orchestrator


def test_input_has_kind(orchestrator: Orchestrator):
    orc_algo = orchestrator.create_algo(category=algo_pb2.ALGO_METRIC)
    backend_algo = algo.Algo("mychannel", orchestrator.client.query_algo(orc_algo.key))

    task_input = MessageToDict(
        computetask_pb2.ComputeTaskInput(identifier=InputIdentifiers.OPENER, asset_key=str(uuid.uuid4())),
        **CONVERT_SETTINGS,
    )

    assert context._input_has_kind(task_input, common_pb2.ASSET_DATA_MANAGER, backend_algo)

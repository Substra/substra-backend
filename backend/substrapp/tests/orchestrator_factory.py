import factory
from google.protobuf.timestamp_pb2 import Timestamp

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.common_pb2 as common_pb2
from substrapp.tests import common

OPEN_PERMISSIONS = common_pb2.Permissions(
    download=common_pb2.Permission(public=True, authorized_ids=[]),
    process=common_pb2.Permission(public=True, authorized_ids=[]),
)

ALGO_INPUTS_PER_CATEGORY = common.ALGO_INPUTS_PER_CATEGORY
ALGO_OUTPUTS_PER_CATEGORY = common.ALGO_OUTPUTS_PER_CATEGORY

DEFAULT_OWNER = "MyOrg1MSP"
DEFAULT_WORKER = "MyOrg1MSP"


def get_storage_address(asset_kind: str, key: str, field: str) -> str:
    return f"http://testserver/{asset_kind}/{key}/{field}/"


class AddressableFactory(factory.Factory):
    class Meta:
        model = common_pb2.Addressable

    checksum = factory.Faker("sha256")
    storage_address = factory.Faker("url")


class AlgoFactory(factory.Factory):
    """Do not use this anymore, please leverage orchestrator.mock module"""

    class Meta:
        model = algo_pb2.Algo

    key = factory.Faker("uuid4")
    name = factory.Faker("user_name")
    category = algo_pb2.ALGO_UNKNOWN
    description = factory.LazyAttribute(
        lambda obj: AddressableFactory(storage_address=get_storage_address("algo", obj.key, "description"))
    )
    algorithm = factory.LazyAttribute(
        lambda obj: AddressableFactory(storage_address=get_storage_address("algo", obj.key, "algorithm"))
    )
    permissions = OPEN_PERMISSIONS
    owner = DEFAULT_OWNER
    creation_date = Timestamp()
    metadata = {}
    inputs = factory.LazyAttribute(lambda obj: ALGO_INPUTS_PER_CATEGORY[obj.category])
    outputs = factory.LazyAttribute(lambda obj: ALGO_OUTPUTS_PER_CATEGORY[obj.category])

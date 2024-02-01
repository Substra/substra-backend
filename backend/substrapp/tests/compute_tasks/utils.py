import orchestrator.mock as orc_mock
from substrapp.compute_tasks import utils


def test_container_image_tag_from_function():
    archive_address = orc_mock.AddressFactory(checksum="test_long_checksum")
    function = orc_mock.FunctionFactory(archive_address=archive_address)

    tag = utils.container_image_tag_from_function(function)
    assert tag == "function-test_long_checks"

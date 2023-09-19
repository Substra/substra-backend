import pytest

import orchestrator
import orchestrator.mock as orc_mock


@pytest.fixture
def function() -> orchestrator.Function:
    return orc_mock.FunctionFactory()

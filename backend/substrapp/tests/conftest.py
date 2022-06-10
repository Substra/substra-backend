import pytest

import substrapp.tests.orchestrator_factory


@pytest.fixture
def orchestrator() -> substrapp.tests.orchestrator_factory.Orchestrator:
    return substrapp.tests.orchestrator_factory.Orchestrator()

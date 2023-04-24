import functools
import pathlib
from typing import Final

import pytest
from django import conf
from rest_framework import test

from api.models import ComputeTask
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedBackendClient
from api.tests.common import AuthenticatedClient

_CHANNEL_NAME: Final[str] = "mychannel"
_EXTRA_HTTP_HEADERS: Final[dict[str, str]] = {"HTTP_SUBSTRA_CHANNEL_NAME": _CHANNEL_NAME}


@pytest.fixture(autouse=True)
def _set_settings(settings: conf.Settings, tmp_path: pathlib.Path):
    settings.MEDIA_ROOT = tmp_path.resolve()
    settings.LEDGER_CHANNELS = {_CHANNEL_NAME: {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}


@pytest.fixture
def authenticated_client() -> test.APIClient:
    client = AuthenticatedClient()

    client.get = functools.partial(client.get, **_EXTRA_HTTP_HEADERS)
    client.post = functools.partial(client.post, **_EXTRA_HTTP_HEADERS)

    return client


@pytest.fixture
def authenticated_backend_client() -> test.APIClient:
    client = AuthenticatedBackendClient()

    client.get = functools.partial(client.get, **_EXTRA_HTTP_HEADERS)
    client.post = functools.partial(client.post, **_EXTRA_HTTP_HEADERS)
    client.put = functools.partial(client.put, **_EXTRA_HTTP_HEADERS)

    return client


@pytest.fixture
def api_client() -> test.APIClient:
    return test.APIClient()


@pytest.fixture
def create_compute_task():
    def _create_compute_task(compute_plan, n_data_sample=4):
        data_manager = factory.create_datamanager()
        data_samples = [factory.create_datasample([data_manager]) for _ in range(n_data_sample)]
        input_keys = {
            "opener": [data_manager.key],
            "datasamples": [data_sample.key for data_sample in data_samples],
        }
        function = factory.create_function(
            inputs=factory.build_function_inputs(["datasamples", "opener", "model"]),
            outputs=factory.build_function_outputs(["model", "performance"]),
            name="simple function",
        )
        return factory.create_computetask(
            compute_plan,
            function,
            inputs=factory.build_computetask_inputs(function, input_keys),
            outputs=factory.build_computetask_outputs(function),
            status=ComputeTask.Status.STATUS_DONE,
        )

    return _create_compute_task


@pytest.fixture
def create_compute_plan(create_compute_task):
    def _create_compute_plan(n_task=20, n_data_sample=4):
        compute_plan = factory.create_computeplan()
        [create_compute_task(compute_plan, n_data_sample=n_data_sample) for _ in range(n_task)]
        return compute_plan

    return _create_compute_plan

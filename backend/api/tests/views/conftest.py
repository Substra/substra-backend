from typing import Optional

import pytest
from rest_framework import test

from api.models import ComputePlan
from api.models import ComputeTask
from api.models import TaskProfiling
from api.tests import asset_factory as factory
from api.tests.common import AuthenticatedBackendClient
from api.tests.common import AuthenticatedClient


@pytest.fixture
def authenticated_client() -> test.APIClient:
    client = AuthenticatedClient()

    return client


@pytest.fixture
def authenticated_backend_client() -> test.APIClient:
    client = AuthenticatedBackendClient()

    return client


@pytest.fixture
def api_client() -> test.APIClient:
    return test.APIClient()


@pytest.fixture
def create_compute_task():
    def _create_compute_task(
        compute_plan: Optional[ComputePlan] = None,
        n_data_sample: int = 4,
        status: ComputeTask.Status = ComputeTask.Status.STATUS_DONE,
    ) -> ComputeTask:
        if not compute_plan:
            compute_plan = factory.create_computeplan()

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
            status=status,
        )

    return _create_compute_task


@pytest.fixture
def create_compute_plan(create_compute_task):
    def _create_compute_plan(n_task: int = 20, n_data_sample: int = 4) -> ComputePlan:
        compute_plan = factory.create_computeplan()
        [create_compute_task(compute_plan, n_data_sample=n_data_sample) for _ in range(n_task)]
        return compute_plan

    return _create_compute_plan


@pytest.fixture
def task_profiling(create_compute_task) -> TaskProfiling:
    task = create_compute_task(status=ComputeTask.Status.STATUS_EXECUTING)
    return factory.create_computetask_profiling(compute_task=task)

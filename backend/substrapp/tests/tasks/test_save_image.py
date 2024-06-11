import pytest

import orchestrator.mock as orc_mock
from builder.exceptions import BuildRetryError
from substrapp.compute_tasks.errors import CeleryNoRetryError
from substrapp.docker_registry import RegistryPreconditionFailedException
from substrapp.tasks.tasks_save_image import save_image_task

CHANNEL = "mychannel"


def test_tasks_save_image_random_exception(celery_app, celery_worker, mocker):
    mocker.patch("image_transfer.make_payload", side_effect=Exception("random error"))
    function = orc_mock.FunctionFactory()
    with pytest.raises(CeleryNoRetryError):
        r = save_image_task.apply_async(
            kwargs={"function_serialized": function.model_dump_json(), "channel_name": CHANNEL}
        )
        r.get()


def test_tasks_save_image_412_exception(celery_app, celery_worker, mocker):
    mocker.patch("image_transfer.make_payload", side_effect=RegistryPreconditionFailedException)
    function = orc_mock.FunctionFactory()
    with pytest.raises(BuildRetryError):
        r = save_image_task.apply(
            kwargs={"function_serialized": function.model_dump_json(), "channel_name": CHANNEL}, retries=1
        )
        r.get()

import os
import tempfile
from unittest import mock

from django.test import override_settings
from grpc import RpcError
from grpc import StatusCode
from parameterized import parameterized
from rest_framework.test import APITestCase

import orchestrator
import orchestrator.mock as orc_mock
from orchestrator.client import OrchestratorClient
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.context import TaskResource
from substrapp.compute_tasks.directories import SANDBOX_DIR
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.save_models import save_models

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
class SaveModelTests(APITestCase):
    @parameterized.expand([("without_exception", False), ("with_exception", True)])
    def test_save_model(self, _, save_model_raise):
        """
        This test ensures that models that are not registered on the orchestrator are not saved
        """
        from substrapp.models import Model

        class FakeDirectories:
            task_dir: str

            def __init__(self, task_dir) -> None:
                self.task_dir = task_dir

        data_dir = tempfile.mkdtemp()
        fake_context = Context(
            channel_name="mychannel",
            task=orc_mock.ComputeTaskFactory(
                category=orchestrator.ComputeTaskCategory.TASK_TRAIN,
                status=orchestrator.ComputeTaskStatus.STATUS_DOING,
                rank=2,
            ),
            compute_plan=None,
            input_assets=[],
            algo={},
            directories=FakeDirectories(data_dir),
            has_chainkeys=False,
        )
        model_dir = os.path.join(data_dir, TaskDirName.OutModels)
        os.makedirs(model_dir)
        model_src = os.path.join(model_dir, Filenames.OutModel)
        fake_context.set_outputs(
            [TaskResource(id="model", value=os.path.join(SANDBOX_DIR, TaskDirName.OutModels, Filenames.OutModel))]
        )
        print(fake_context._outputs)

        with open(model_src, "w") as f:
            f.write("model content")

        error = RpcError()
        error.details = "orchestrator unavailable"
        error.code = lambda: StatusCode.UNAVAILABLE

        with mock.patch.object(OrchestratorClient, "register_models") as mregister_model, mock.patch(
            "substrapp.compute_tasks.save_models.add_model_from_path"
        ):

            if save_model_raise:
                mregister_model.side_effect = error

            try:
                save_models(fake_context)
            except RpcError as e:
                if not save_model_raise:
                    # exception expected
                    raise e

        models = Model.objects.all()
        filtered_model_keys = [str(model.key) for model in models]
        self.assertEqual(len(filtered_model_keys), 0 if save_model_raise else 1)

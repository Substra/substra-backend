import os
import tempfile
import uuid

import mock
from django.test import override_settings
from grpc import RpcError
from grpc import StatusCode
from parameterized import parameterized
from rest_framework.test import APITestCase

import orchestrator.model_pb2 as model_pb2
from orchestrator.client import OrchestratorClient
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.save_models import _save_model

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT, LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}
)
class SaveModelTests(APITestCase):
    @parameterized.expand([("without_exception", False), ("with_exception", True)])
    def test_save_model(self, _, save_model_raise):
        """
        This test ensures that models that are not registered on the orchestrator are not saved
        """
        from substrapp.models import Model

        task_key = str(uuid.uuid4())
        model_dir = tempfile.mkdtemp()
        model_src = os.path.join(model_dir, Filenames.OutModel)

        with open(model_src, "w") as f:
            f.write("model content")

        error = RpcError()
        error.details = "orchestrator unavailable"
        error.code = lambda: StatusCode.UNAVAILABLE

        with mock.patch.object(OrchestratorClient, "register_model") as mregister_model:

            if save_model_raise:
                mregister_model.side_effect = error

            try:
                _save_model("mychannel", model_pb2.MODEL_SIMPLE, model_src, task_key)
            except RpcError as e:
                if not save_model_raise:
                    # exception expected
                    raise e

        models = Model.objects.all()
        filtered_model_keys = [str(model.key) for model in models]
        self.assertEqual(len(filtered_model_keys), 0 if save_model_raise else 1)

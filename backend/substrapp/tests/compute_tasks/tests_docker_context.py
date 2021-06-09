import mock
import uuid

from rest_framework.test import APITestCase
from substrapp.compute_tasks.docker_context import _get_algo, _get_objective

CHANNEL = "mychannel"


class DockerContextTests(APITestCase):
    def test_get_algo(self):
        algo_content = b"123"

        with mock.patch("substrapp.compute_tasks.docker_context.get_asset_content") as mget_asset_content, mock.patch(
            "substrapp.compute_tasks.docker_context.get_object_from_ledger"
        ):
            mget_asset_content.return_value = algo_content

            data = _get_algo(CHANNEL, "traintuple", "algo key")
            self.assertEqual(algo_content, data)

    def test_get_objective(self):
        metrics_content = b"123"
        objective_key = uuid.uuid4()

        with mock.patch("substrapp.compute_tasks.docker_context.get_asset_content") as mget_asset_content, mock.patch(
            "substrapp.compute_tasks.docker_context.get_object_from_ledger"
        ):

            mget_asset_content.return_value = metrics_content

            objective = _get_objective(CHANNEL, {"objective": {"key": objective_key, "metrics": ""}})
            self.assertTrue(isinstance(objective, bytes))
            self.assertEqual(objective, metrics_content)

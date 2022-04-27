import pathlib
import tempfile
import unittest
import uuid
from unittest import mock

from parameterized import parameterized

import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.compute_tasks.algo import Algo
from substrapp.compute_tasks.image_builder import _get_entrypoint_from_dockerfile
from substrapp.compute_tasks.image_builder import build_images

DOCKERFILE = """
FROM ubuntu:16.04
RUN echo "Hello World"
ENTRYPOINT ["python3", "myalgo.py"]
"""


class GetEntrypointFromDockerfileTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_dir = pathlib.Path(self._tmp_dir.name)
        self.dockerfile_path = self.tmp_dir / "Dockerfile"

    def tearDown(self):
        self._tmp_dir.cleanup()

    def test_get_entrypoint_from_dockerfile(self):
        self.dockerfile_path.write_text(DOCKERFILE)
        res = _get_entrypoint_from_dockerfile(self.tmp_dir)
        self.assertEqual(res, ["python3", "myalgo.py"])

    @parameterized.expand(
        [
            ("INVALID DOCKERFILE", "^Invalid Dockerfile: Cannot find ENTRYPOINT$"),
            ("FROM scratch\nENTRYPOINT invalid_entrypoint_form", "^Invalid ENTRYPOINT.+"),
        ],
    )
    def test_get_entrypoint_from_dockerfile_raise(self, dockerfile: str, exc_regex: str):
        self.dockerfile_path.write_text(dockerfile)

        with self.assertRaisesRegex(compute_task_errors.BuildError, exc_regex):
            _get_entrypoint_from_dockerfile(self.tmp_dir)


class TestImageBuilder:
    @parameterized.expand([("train_task", computetask_pb2.TASK_TRAIN), ("test_task", computetask_pb2.TASK_TEST)])
    def test_build_images(self, _, task_category):

        algo_key = str(uuid.uuid4())
        algo_image_tag = f"algo-{algo_key[0:8]}"
        algo_owner = "algo owner"
        algo_storage_address = "algo storage_address"
        algo_checksum = "algo checksum"

        metric1_key = str(uuid.uuid4())
        metric1_image_tag = f"algo-{metric1_key[0:8]}"
        metric1_owner = "metric1 owner"
        metric1_storage_address = "metric1 storage_address"
        metric1_checksum = "metric1 checksum"

        metric2_key = str(uuid.uuid4())
        metric2_image_tag = f"algo-{metric2_key[0:8]}"
        metric2_owner = "metric2 owner"
        metric2_storage_address = "metric2 storage_address"
        metric2_checksum = "metric2 checksum"

        channel_name = "mychannel"

        algo = {
            "key": algo_key,
            "owner": algo_owner,
            "algorithm": {"storage_address": algo_storage_address, "checksum": algo_checksum},
        }
        metric1 = {
            "key": metric1_key,
            "owner": metric1_owner,
            "algorithm": {"storage_address": metric1_storage_address, "checksum": metric1_checksum},
        }
        metric2 = {
            "key": metric2_key,
            "owner": metric2_owner,
            "algorithm": {"storage_address": metric2_storage_address, "checksum": metric2_checksum},
        }

        if task_category == computetask_pb2.TASK_TRAIN:
            all_algos = [Algo(channel_name, algo)]
        else:
            all_algos = [Algo(channel_name, algo), Algo(channel_name, metric1), Algo(channel_name, metric2)]

        with (
            mock.patch("substrapp.compute_tasks.image_builder._build_asset_image") as m_build_asset_image,
            mock.patch("substrapp.compute_tasks.image_builder.container_image_exists") as mcontainer_image_exists,
        ):

            mcontainer_image_exists.return_value = False
            build_images(all_algos)

            if task_category == computetask_pb2.TASK_TEST:

                assert mcontainer_image_exists.call_count == 3
                mcontainer_image_exists.assert_any_call(algo_image_tag)
                mcontainer_image_exists.assert_any_call(metric1_image_tag)
                mcontainer_image_exists.assert_any_call(metric2_image_tag)

                assert m_build_asset_image.call_count == 3
                m_build_asset_image.assert_any_call(all_algos[0])
                m_build_asset_image.assert_any_call(all_algos[1])
                m_build_asset_image.assert_any_call(all_algos[2])

            else:
                assert mcontainer_image_exists.call_count == 1
                mcontainer_image_exists.assert_any_call(algo_image_tag)

                assert m_build_asset_image.call_count == 1
                m_build_asset_image.assert_any_call(all_algos[0])

import pathlib
import tempfile
import unittest
import uuid
from unittest import mock

from parameterized import parameterized

from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.compute_tasks.algo import Algo
from substrapp.compute_tasks.image_builder import _get_entrypoint_from_dockerfile
from substrapp.compute_tasks.image_builder import build_image_if_missing
from substrapp.tests.test_utils import CHANNEL

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
    def test_build_image_if_missing(self):
        algo_key = str(uuid.uuid4())
        algo_owner = "algo owner"
        algo_storage_address = "algo storage_address"
        algo_checksum = "algo checksum"
        algo_image_tag = f"algo-{algo_checksum}"

        algo = Algo(
            CHANNEL,
            {
                "key": algo_key,
                "owner": algo_owner,
                "algorithm": {"storage_address": algo_storage_address, "checksum": algo_checksum},
            },
        )

        with (
            mock.patch("substrapp.compute_tasks.image_builder._build_asset_image") as m_build_asset_image,
            mock.patch("substrapp.compute_tasks.image_builder.container_image_exists") as mcontainer_image_exists,
        ):

            mcontainer_image_exists.return_value = False
            build_image_if_missing(algo)

            assert mcontainer_image_exists.call_count == 1
            mcontainer_image_exists.assert_any_call(algo_image_tag)

            assert m_build_asset_image.call_count == 1
            m_build_asset_image.assert_any_call(algo)

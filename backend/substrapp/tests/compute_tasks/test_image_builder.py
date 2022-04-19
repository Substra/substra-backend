import json
import pathlib
import tempfile
import unittest
import uuid
from unittest import mock

from django.test.utils import override_settings
from parameterized import parameterized
from rest_framework.test import APITestCase

import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.compute_tasks.image_builder import _build_asset_image
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


class ImageBuilderTests(APITestCase):
    @parameterized.expand([("train_task", computetask_pb2.TASK_TRAIN), ("test_task", computetask_pb2.TASK_TEST)])
    def test_build_images(self, _, task_category_):

        algo_key_ = str(uuid.uuid4())
        algo_image_tag_ = "algo_image_tag"
        algo_owner = "algo owner"
        algo_storage_address = "algo storage_address"
        algo_checksum = "algo checksum"

        metric1_key = str(uuid.uuid4())
        metric1_image_tag = "metric1_image_tag"
        metric1_owner = "metric1 owner"
        metric1_storage_address = "metric1 storage_address"
        metric1_checksum = "metric1 checksum"

        metric2_key = str(uuid.uuid4())
        metric2_image_tag = "metric2_image_tag"
        metric2_owner = "metric2 owner"
        metric2_storage_address = "metric2 storage_address"
        metric2_checksum = "metric2 checksum"

        class FakeContext:
            task_category = task_category_
            metrics = {
                metric1_key: {
                    "key": metric1_key,
                    "owner": metric1_owner,
                    "algorithm": {"storage_address": metric1_storage_address, "checksum": metric1_checksum},
                },
                metric2_key: {
                    "key": metric1_key,
                    "owner": metric2_owner,
                    "algorithm": {"storage_address": metric2_storage_address, "checksum": metric2_checksum},
                },
            }
            metrics_image_tags = {
                metric1_key: metric1_image_tag,
                metric2_key: metric2_image_tag,
            }
            algo_key = algo_key_
            algo = {
                "key": algo_key,
                "owner": algo_owner,
                "algorithm": {"storage_address": algo_storage_address, "checksum": algo_checksum},
            }
            algo_image_tag = algo_image_tag_

        ctx = FakeContext()

        with (
            mock.patch("substrapp.compute_tasks.image_builder._build_asset_image") as m_build_asset_image,
            mock.patch("substrapp.compute_tasks.image_builder.container_image_exists") as mcontainer_image_exists,
        ):

            mcontainer_image_exists.return_value = False
            build_images(ctx)

            if task_category_ == computetask_pb2.TASK_TEST:

                self.assertEqual(mcontainer_image_exists.call_count, 3)
                mcontainer_image_exists.assert_any_call(algo_image_tag_)
                mcontainer_image_exists.assert_any_call(metric1_image_tag)
                mcontainer_image_exists.assert_any_call(metric2_image_tag)

                self.assertEqual(m_build_asset_image.call_count, 3)
                m_build_asset_image.assert_any_call(
                    ctx, algo_image_tag_, algo_key_, algo_storage_address, algo_owner, algo_checksum
                )
                m_build_asset_image.assert_any_call(
                    ctx, metric1_image_tag, metric1_key, metric1_storage_address, metric1_owner, metric1_checksum
                )
                m_build_asset_image.assert_any_call(
                    ctx, metric2_image_tag, metric2_key, metric2_storage_address, metric2_owner, metric2_checksum
                )

            else:
                self.assertEqual(mcontainer_image_exists.call_count, 1)
                mcontainer_image_exists.assert_any_call(algo_image_tag_)

                self.assertEqual(m_build_asset_image.call_count, 1)
                m_build_asset_image.assert_any_call(
                    ctx, algo_image_tag_, algo_key_, algo_storage_address, algo_owner, algo_checksum
                )

    @override_settings(SUBTUPLE_TMP_DIR=tempfile.mkdtemp())
    def test_build_asset_image(self):

        channel_name_ = "mychannel"

        class FakeContext:
            channel_name = channel_name_

        ctx = FakeContext()
        tmp_dir = {"tmp directory": ""}
        asset_key = "asset key"
        asset_content = b"zipped content"
        storage_address = "storage_address"
        owner = "owner"
        checksum = "checksum"
        image_tag = "image_tag"
        entrypoint = ["some", "entrypoint"]

        with (
            mock.patch("substrapp.compute_tasks.image_builder.TemporaryDirectory") as mtemporary_directory,
            mock.patch("substrapp.compute_tasks.image_builder.node_client.get") as m_get_asset_content,
            mock.patch("substrapp.compute_tasks.image_builder.uncompress_content") as muncompress_content,
            mock.patch(
                "substrapp.compute_tasks.image_builder._get_entrypoint_from_dockerfile"
            ) as m_get_entrypoint_from_dockerfile,
            mock.patch("substrapp.compute_tasks.image_builder._build_container_image") as m_build_container_image,
            mock.patch("substrapp.compute_tasks.image_builder.ImageEntrypoint.objects.get_or_create") as mget_or_create,
        ):

            mtemporary_directory.return_value.__enter__.return_value = tmp_dir
            m_get_asset_content.return_value = asset_content
            m_get_entrypoint_from_dockerfile.return_value = entrypoint

            _build_asset_image(ctx, image_tag, asset_key, storage_address, owner, checksum)

            m_get_asset_content.assert_called_once_with(channel_name_, owner, storage_address, checksum)
            muncompress_content.assert_called_once_with(asset_content, tmp_dir)
            m_get_entrypoint_from_dockerfile.assert_called_once_with(tmp_dir)
            m_build_container_image.assert_called_once_with(tmp_dir, image_tag)
            mget_or_create.assert_called_once_with(asset_key=asset_key, entrypoint_json=json.dumps(entrypoint))

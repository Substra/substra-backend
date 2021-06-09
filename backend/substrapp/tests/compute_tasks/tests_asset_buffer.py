import os
import shutil
import mock
import tempfile

from django.test import override_settings
from parameterized import parameterized
from rest_framework.test import APITestCase

from ..common import FakeModel, FakeDataManager, FakeDataSample
from substrapp.utils import get_dir_hash, get_hash
from substrapp.compute_tasks.directories import AssetBufferDirName
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.asset_buffer import (
    _add_datasamples_to_buffer,
    _add_opener_to_buffer,
    _add_model_to_buffer,
    _add_assets_to_taskdir,
)
from substrapp.compute_tasks.directories import TaskDirName, CPDirName
from substrapp.compute_tasks.asset_buffer import init_asset_buffer

ASSET_BUFFER_DIR = tempfile.mkdtemp()
CHANNEL = "mychannel"


@override_settings(ASSET_BUFFER_DIR=ASSET_BUFFER_DIR)
class AssetBufferTests(APITestCase):
    def setUp(self):
        init_asset_buffer()
        self._setup_directories()
        self._setup_opener()
        self._setup_data_sample()
        self._setup_model()

    def _setup_directories(self):
        self.cp_dir = tempfile.mkdtemp()
        self.task_dir = tempfile.mkdtemp()

        class FakeDirectories:
            compute_plan_dir = self.cp_dir
            task_dir = self.task_dir

        self.dirs = FakeDirectories()

    def _setup_opener(self):
        self.dataset_key = "some_dataset_key"
        self.opener_contents = "opener contents"
        self.opener_path = os.path.join(tempfile.mkdtemp(), "opener.py")

        with open(self.opener_path, "w") as f:
            f.write(self.opener_contents)

        self.opener_checksum = get_hash(self.opener_path)

    def _setup_data_sample(self):
        self.data_sample_dir = tempfile.mkdtemp()
        self.data_sample_filename = "datasample.csv"
        self.data_sample_path = os.path.join(self.data_sample_dir, self.data_sample_filename)
        self.data_sample_contents = "data sample contents"
        self.data_sample_key = "some_data_sample_key"

        with open(self.data_sample_path, "w") as f:
            f.write(self.data_sample_contents)

        self.data_sample_checksum = get_dir_hash(self.data_sample_dir)

    def _setup_model(self):
        self.model_key = "some_model_key"
        self.model_contents = "model contents"
        self.model_path = os.path.join(tempfile.mkdtemp(), "mymodel")
        self.model_traintuple_key = "some traintuple key"

        with open(self.model_path, "w") as f:
            f.write(self.model_contents)

        self.model_checksum = get_hash(self.model_path, self.model_traintuple_key)

    def test_populate_buffer_opener(self):
        with mock.patch("substrapp.models.DataManager.objects.get") as mget:

            # Test 1: DB is empty
            with self.assertRaises(Exception):
                _add_opener_to_buffer(self.dataset_key, self.opener_checksum)

            # Test 2: OK
            mget.return_value = FakeDataManager(self.opener_path)

            _add_opener_to_buffer(self.dataset_key, self.opener_checksum)

            dest = os.path.join(ASSET_BUFFER_DIR, AssetBufferDirName.Openers, self.dataset_key, Filenames.Opener)
            with open(dest) as f:
                contents = f.read()
                self.assertEqual(contents, self.opener_contents)

            os.remove(dest)  # delete file, otherwise next call to _populate_buffer_opener will be a noop

            # Test 3: File corrupted
            with open(self.opener_path, "a+") as f:
                f.write("corrupted")

            with self.assertRaises(Exception):
                _add_opener_to_buffer(self.dataset_key, self.opener_checksum)

    def test_populate_buffer_data_samples(self):

        with mock.patch("substrapp.models.DataSample.objects.get") as mget:

            # Test 1: DB is empty
            with self.assertRaises(Exception):
                _add_datasamples_to_buffer([self.data_sample_key])

            # Test 2: OK
            mget.return_value = FakeDataSample(self.data_sample_dir, self.data_sample_checksum)

            _add_datasamples_to_buffer([self.data_sample_key])

            dest = os.path.join(ASSET_BUFFER_DIR, AssetBufferDirName.Datasamples, self.data_sample_key)
            with open(os.path.join(dest, self.data_sample_filename)) as f:
                contents = f.read()
                self.assertEqual(contents, self.data_sample_contents)

            shutil.rmtree(dest)  # delete folder, otherwise next call to _populate_buffer_data_samples will be a noop

            # Test 3: File corrupted
            with open(self.data_sample_path, "a+") as f:
                f.write("corrupted")

            with self.assertRaises(Exception):
                _add_datasamples_to_buffer([self.data_sample_key])

    @parameterized.expand(
        [
            ("composite_head_model", True),
            ("non_composite_head_model", False),
        ]
    )
    def test_add_model_to_buffer(self, _, is_head_model):

        dest = os.path.join(ASSET_BUFFER_DIR, AssetBufferDirName.Models, self.model_key)

        model = {
            "key": self.model_key,
            "traintuple_key": self.model_traintuple_key,
        }

        if is_head_model:

            with mock.patch("substrapp.models.Model.objects.get") as mget:

                # Test 1: DB is empty
                with self.assertRaises(Exception):
                    _add_model_to_buffer(CHANNEL, model)

                # Test 2: OK
                mget.return_value = FakeModel(self.model_path, self.model_checksum)
                _add_model_to_buffer(CHANNEL, model)

                with open(dest) as f:
                    contents = f.read()
                    self.assertEqual(contents, self.model_contents)

                os.remove(dest)  # delete file, otherwise next call to _add_model_to_buffer will be a noop

                # Test 3: File corrupted
                with open(self.model_path, "a+") as f:
                    f.write("corrupted")

                with self.assertRaises(Exception):
                    _add_model_to_buffer(CHANNEL, model)

        else:
            node_id = "node id"
            storage_address = "some storage address"

            model["storage_address"] = storage_address
            model["checksum"] = self.model_checksum

            with mock.patch(
                "substrapp.compute_tasks.asset_buffer._find_training_step_tuple_from_key"
            ) as mfind_training_step_tuple_from_key, mock.patch(
                "substrapp.compute_tasks.asset_buffer._get_tuple_owner"
            ) as mget_tuple_owner, mock.patch(
                "substrapp.compute_tasks.asset_buffer.get_and_put_asset_content"
            ) as mget_and_put_asset_content:

                mfind_training_step_tuple_from_key.return_value = ("tuple_type", "metadata")
                mget_tuple_owner.return_value = node_id

                _add_model_to_buffer(CHANNEL, model)

                mget_and_put_asset_content.assert_called_once_with(
                    CHANNEL, storage_address, node_id, self.model_checksum, dest, self.model_traintuple_key
                )

    def test_move_assets_from_buffer_to_taskdir_data_sample(self):

        # populate the buffer
        with mock.patch("substrapp.models.DataSample.objects.get") as mget:
            mget.return_value = FakeDataSample(self.data_sample_dir, self.data_sample_checksum)
            _add_datasamples_to_buffer([self.data_sample_key])

        # load from buffer into task dir
        dest = os.path.join(
            self.dirs.task_dir, TaskDirName.Datasamples, self.data_sample_key, self.data_sample_filename
        )
        _add_assets_to_taskdir(self.dirs, CPDirName.Datasamples, TaskDirName.Datasamples, [self.data_sample_key])

        # check task dir
        with open(dest) as f:
            contents = f.read()
            self.assertEqual(contents, self.data_sample_contents)

    def test_move_assets_from_buffer_to_taskdir_model(self):

        # populate the buffer
        model = {
            "key": self.model_key,
            "traintuple_key": "traintuple_key",
        }
        with mock.patch("substrapp.models.Model.objects.get") as mget:
            mget.return_value = FakeModel(self.model_path, self.model_checksum)
            _add_model_to_buffer(CHANNEL, model)

        # load from buffer into task dir
        dest = os.path.join(self.dirs.task_dir, TaskDirName.InModels, self.model_key)
        _add_assets_to_taskdir(self.dirs, CPDirName.Models, TaskDirName.InModels, [self.model_key])

        # check task dir
        with open(dest) as f:
            contents = f.read()
            self.assertEqual(contents, self.model_contents)

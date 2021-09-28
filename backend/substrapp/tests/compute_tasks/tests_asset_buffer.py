import uuid
import os
import shutil
import mock
import tempfile

from django.test import override_settings
from parameterized import parameterized
from rest_framework.test import APITestCase

from ..common import FakeModel, FakeDataSample
from substrapp.utils import get_dir_hash, get_hash
from substrapp.compute_tasks.directories import AssetBufferDirName, init_task_dirs
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.asset_buffer import (
    _add_datasamples_to_buffer,
    _add_opener_to_buffer,
    _add_model_to_buffer,
    _add_assets_to_taskdir,
    _download_algo,
    _download_objective,
)
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.asset_buffer import init_asset_buffer
import orchestrator.computetask_pb2 as computetask_pb2

ASSET_BUFFER_DIR = tempfile.mkdtemp()
ASSET_BUFFER_DIR_1 = tempfile.mkdtemp()
ASSET_BUFFER_DIR_2 = tempfile.mkdtemp()
ASSET_BUFFER_DIR_3 = tempfile.mkdtemp()
CHANNEL = "mychannel"
NUM_DATA_SAMPLES = 3


class TestDataSample:
    key: uuid.uuid4
    dir: str
    filename: str
    path: str
    contents: str
    checksum: str

    @classmethod
    def create(cls, index: int):
        res = TestDataSample()
        res.key = str(uuid.uuid4())
        res.dir = tempfile.mkdtemp()
        res.filename = "datasample.csv"
        res.path = os.path.join(res.dir, res.filename)
        res.contents = f"data sample contents {index}"

        with open(res.path, "w") as f:
            f.write(res.contents)

        res.checksum = get_dir_hash(res.dir)

        return res

    def to_fake_data_sample(self):
        return FakeDataSample(self.dir, self.checksum)


@override_settings(ASSET_BUFFER_DIR=ASSET_BUFFER_DIR,
                   MEDIA_ROOT=tempfile.mkdtemp(),
                   LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}})
class AssetBufferTests(APITestCase):
    def setUp(self):
        self._setup_directories()
        self._setup_opener()
        self._setup_data_samples()
        self._setup_model()
        self._setup_context()

    def _setup_directories(self):
        self.cp_dir = tempfile.mkdtemp()
        self.task_dir = tempfile.mkdtemp()

        class FakeDirectories:
            compute_plan_dir = self.cp_dir
            task_dir = self.task_dir

        self.dirs = FakeDirectories()
        init_task_dirs(self.dirs)

    def _setup_opener(self):
        self.opener_contents = "opener contents"
        self.opener_path = os.path.join(tempfile.mkdtemp(), "opener.py")

        with open(self.opener_path, "w") as f:
            f.write(self.opener_contents)

        self.opener_checksum = get_hash(self.opener_path)
        self.opener_storage_address = "some storage address"
        self.data_manager_key = "some_data_manager_key"
        self.data_manager = {
            "key": self.data_manager_key,
            "opener": {
                "storage_address": self.opener_storage_address,
                "checksum": self.opener_checksum,
            },
        }

    def _setup_data_samples(self):
        self.data_samples = {}
        for i in range(NUM_DATA_SAMPLES):
            data_sample = TestDataSample.create(i)
            self.data_samples[data_sample.key] = data_sample

    def _setup_model(self):
        self.model_key = str(uuid.uuid4())
        self.model_contents = "model contents"
        self.model_path = os.path.join(tempfile.mkdtemp(), "mymodel")
        self.model_compute_task_key = "some compute task key"

        with open(self.model_path, "w") as f:
            f.write(self.model_contents)

        self.model_checksum = get_hash(self.model_path, self.model_compute_task_key)

    def _setup_context(self):
        class FakeContext:
            directories = self.dirs
            channel_name = CHANNEL
            compute_plan_key = "some compute plan key"
            task_category = computetask_pb2.TASK_TRAIN
            objective = {'key': str(uuid.uuid4()),
                         'owner': 'test',
                         'metrics': {'storage_address': 'test', 'checksum': 'check'}}
            algo = {'key': str(uuid.uuid4()),
                    'owner': 'test',
                    'algorithm': {'storage_address': 'test', 'checksum': 'check'}}

        self.ctx = FakeContext()

    def _attempt(self):
        return self.retries + 1

    @override_settings(ASSET_BUFFER_DIR=ASSET_BUFFER_DIR_1)
    def test_add_opener_to_buffer(self):

        init_asset_buffer()
        node_id = "node id"

        dest = os.path.join(ASSET_BUFFER_DIR_1, AssetBufferDirName.Openers, self.data_manager_key, Filenames.Opener)

        with mock.patch(
            "substrapp.compute_tasks.asset_buffer.get_and_put_asset_content"
        ) as mget_and_put_asset_content, mock.patch("substrapp.compute_tasks.asset_buffer.get_owner") as mget_owner:

            mget_owner.return_value = node_id

            _add_opener_to_buffer(CHANNEL, self.data_manager)

            mget_and_put_asset_content.assert_called_once_with(
                CHANNEL, self.opener_storage_address, node_id, self.opener_checksum, dest, hash_key=None
            )

    @override_settings(ASSET_BUFFER_DIR=ASSET_BUFFER_DIR_2)
    def test_add_datasamples_to_buffer(self):

        init_asset_buffer()
        with mock.patch("substrapp.models.DataSample.objects.get") as mget:
            data_samples = list(self.data_samples.values())

            # Test 1: DB is empty
            with self.assertRaises(Exception):
                _add_datasamples_to_buffer([self.data_samples.keys()[0]])

            # Test 2: OK
            mget.side_effect = lambda key: self.data_samples[key].to_fake_data_sample()

            # Add one of the data samples twice, to check that scenario
            _add_datasamples_to_buffer(list(self.data_samples.keys())[:2])  # add samples 0 and 1
            _add_datasamples_to_buffer(list(self.data_samples.keys())[1:])  # add samples 1 and 2

            for i in range(NUM_DATA_SAMPLES):
                data_sample = data_samples[i]
                dest = os.path.join(ASSET_BUFFER_DIR_2, AssetBufferDirName.Datasamples, data_sample.key)
                with open(os.path.join(dest, data_sample.filename)) as f:
                    contents = f.read()
                    self.assertEqual(contents, data_sample.contents)
                shutil.rmtree(dest)  # delete folder, otherwise next call to _add_datasamples_to_buffer will be a noop

            # Test 3: File corrupted
            with open(data_samples[0].path, "a+") as f:
                f.write("corrupted")
            with self.assertRaises(Exception):
                _add_datasamples_to_buffer([data_samples[0].key])

    @parameterized.expand(
        [
            ("composite_head_model", True),
            ("non_composite_head_model", False),
        ]
    )
    @override_settings(ASSET_BUFFER_DIR=ASSET_BUFFER_DIR_3)
    def test_add_model_to_buffer(self, _, is_head_model):

        init_asset_buffer()
        dest = os.path.join(ASSET_BUFFER_DIR_3, AssetBufferDirName.Models, self.model_key)

        model = {
            "key": self.model_key,
            "compute_task_key": self.model_compute_task_key,
        }

        if is_head_model:

            with mock.patch("substrapp.models.Model.objects.get") as mget:

                # Test 1: DB is empty
                with self.assertRaises(Exception):
                    _add_model_to_buffer(CHANNEL, model, "node 1")

                # Test 2: OK
                mget.return_value = FakeModel(self.model_path, self.model_checksum)
                _add_model_to_buffer(CHANNEL, model, "node 1")

                with open(dest) as f:
                    contents = f.read()
                    self.assertEqual(contents, self.model_contents)

                os.remove(dest)  # delete file, otherwise next call to _add_model_to_buffer will be a noop

                # Test 3: File corrupted
                with open(self.model_path, "a+") as f:
                    f.write("corrupted")

                with self.assertRaises(Exception):
                    _add_model_to_buffer(CHANNEL, model, "node 1")

        else:
            node_id = "node 1"
            storage_address = "some storage address"

            model['address'] = {"storage_address": storage_address,
                                "checksum": self.model_checksum}

            with mock.patch(
                "substrapp.compute_tasks.asset_buffer.get_and_put_asset_content"
            ) as mget_and_put_asset_content:

                _add_model_to_buffer(CHANNEL, model, node_id)

                mget_and_put_asset_content.assert_called_once_with(
                    CHANNEL, storage_address, node_id, self.model_checksum, dest, self.model_compute_task_key
                )

    def test_add_assets_to_taskdir_data_sample(self):
        data_samples = list(self.data_samples.values())

        # populate the buffer
        init_asset_buffer()
        with mock.patch("substrapp.models.DataSample.objects.get") as mget:
            mget.side_effect = lambda key: self.data_samples[key].to_fake_data_sample()
            _add_datasamples_to_buffer(self.data_samples.keys())

        # load from buffer into task dir
        _add_assets_to_taskdir(
            self.dirs, AssetBufferDirName.Datasamples, TaskDirName.Datasamples, self.data_samples.keys()
        )

        # check task dir
        for i in range(NUM_DATA_SAMPLES):
            data_sample = data_samples[i]
            dest = os.path.join(self.dirs.task_dir, TaskDirName.Datasamples, data_sample.key, data_sample.filename)
            with open(dest) as f:
                contents = f.read()
                self.assertEqual(contents, data_sample.contents)

    def test_add_assets_to_taskdir_model(self):

        # populate the buffer
        init_asset_buffer()
        model = {
            "key": self.model_key,
            "compute_task_key": self.model_compute_task_key,
        }
        with mock.patch("substrapp.models.Model.objects.get") as mget:
            mget.return_value = FakeModel(self.model_path, self.model_checksum)
            _add_model_to_buffer(CHANNEL, model, "node 1")

        # load from buffer into task dir
        dest = os.path.join(self.dirs.task_dir, TaskDirName.InModels, self.model_key)
        _add_assets_to_taskdir(self.dirs, AssetBufferDirName.Models, TaskDirName.InModels, [self.model_key])

        # check task dir
        with open(dest) as f:
            contents = f.read()
            self.assertEqual(contents, self.model_contents)

    def test_download_algo(self):

        algo_content = b"123"

        with mock.patch("substrapp.compute_tasks.asset_buffer.get_asset_content") as mget_asset_content:
            mget_asset_content.return_value = algo_content

            data = _download_algo(self.ctx)
            self.assertEqual(algo_content, data)

    def test_download_objective(self):

        metrics_content = b"123"
        with mock.patch("substrapp.compute_tasks.asset_buffer.get_asset_content") as mget_asset_content:

            mget_asset_content.return_value = metrics_content

            objective = _download_objective(self.ctx)
            self.assertTrue(isinstance(objective, bytes))
            self.assertEqual(objective, metrics_content)

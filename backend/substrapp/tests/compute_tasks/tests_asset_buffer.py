import os
import shutil
import tempfile
import uuid
from abc import ABCMeta
from abc import abstractmethod
from collections import ChainMap
from unittest import mock

from django.core.files import File
from django.test import override_settings
from parameterized import parameterized
from rest_framework.test import APITestCase

import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.compute_tasks.asset_buffer import _add_assets_to_taskdir
from substrapp.compute_tasks.asset_buffer import _add_datasamples_to_buffer
from substrapp.compute_tasks.asset_buffer import _add_model_to_buffer
from substrapp.compute_tasks.asset_buffer import _add_opener_to_buffer
from substrapp.compute_tasks.asset_buffer import _download_algo
from substrapp.compute_tasks.asset_buffer import _download_metric
from substrapp.compute_tasks.asset_buffer import init_asset_buffer
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.directories import AssetBufferDirName
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.directories import init_task_dirs
from substrapp.utils import get_dir_hash
from substrapp.utils import get_hash

from ..common import FakeDataSample
from ..common import FakeModel

ASSET_BUFFER_DIR = tempfile.mkdtemp()
ASSET_BUFFER_DIR_1 = tempfile.mkdtemp()
ASSET_BUFFER_DIR_2 = tempfile.mkdtemp()
ASSET_BUFFER_DIR_3 = tempfile.mkdtemp()
CHANNEL = "mychannel"
NUM_DATA_SAMPLES = 2 * 3  # half will be registered via a path in the db, the other half by a file


class TestDataSample(metaclass=ABCMeta):
    key: uuid.uuid4
    filename: str
    contents: str
    checksum: str

    @classmethod
    def create(cls, index: int):
        res = cls()
        res.key = str(uuid.uuid4())
        res.filename = "datasample.csv"
        res.contents = f"data sample contents {index}"
        return res

    @abstractmethod
    def to_fake_data_sample(self):
        raise NotImplementedError

    @abstractmethod
    def falsify_content(self, new_content):
        raise NotImplementedError


class TestDataSampleSavedByPath(TestDataSample):
    _dir: str
    _path: str

    @classmethod
    def create(cls, index: int):
        res = super().create(index)
        res._dir = tempfile.mkdtemp()
        res._path = os.path.join(res._dir, res.filename)

        with open(res._path, "w") as f:
            f.write(res.contents)

        res.checksum = get_dir_hash(res._dir)

        return res

    def to_fake_data_sample(self):
        return FakeDataSample(path=self._dir, checksum=self.checksum)

    def falsify_content(self, new_content):
        self.contents = new_content
        with open(self._path, "w") as f:
            f.write(self.contents)


class TestDataSampleSavedByFile(TestDataSample):
    _archive_path: str

    @classmethod
    def create(cls, index: int):
        res = super().create(index)
        archive_dir = tempfile.mkdtemp()
        uncompressed_dir = tempfile.mkdtemp()
        uncompressed_file_path = os.path.join(uncompressed_dir, res.filename)

        with open(uncompressed_file_path, "w") as f:
            f.write(res.contents)

        res._archive_path = shutil.make_archive(archive_dir, "tar", root_dir=uncompressed_dir)

        with tempfile.TemporaryDirectory() as tmp_path:
            shutil.unpack_archive(res._archive_path, tmp_path)
            res.checksum = get_dir_hash(tmp_path)

        return res

    def to_fake_data_sample(self):
        return FakeDataSample(file=File(open(self._archive_path, "rb")), checksum=self.checksum)

    def falsify_content(self, new_content):
        self.contents = new_content
        archive_dir = tempfile.mkdtemp()
        uncompressed_dir = tempfile.mkdtemp()
        uncompressed_file_path = os.path.join(uncompressed_dir, self.filename)

        with open(uncompressed_file_path, "w") as f:
            f.write(self.contents)

        self._archive_path = shutil.make_archive(archive_dir, "tar", root_dir=uncompressed_dir)


@override_settings(
    ASSET_BUFFER_DIR=ASSET_BUFFER_DIR,
    LEDGER_CHANNELS={"mychannel": {"chaincode": {"name": "mycc"}, "model_export_enabled": True}},
)
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
        # half are registered in the db by a path
        self.data_samples_saved_as_path = {}
        for i in range(NUM_DATA_SAMPLES // 2):
            data_sample = TestDataSampleSavedByPath.create(i)
            self.data_samples_saved_as_path[data_sample.key] = data_sample

        # half are registered in the db by a file
        self.data_samples_saved_as_file = {}
        for i in range(int(NUM_DATA_SAMPLES / 2)):
            data_sample = TestDataSampleSavedByFile.create(i)
            self.data_samples_saved_as_file[data_sample.key] = data_sample

        self.data_samples = dict(ChainMap(self.data_samples_saved_as_path, self.data_samples_saved_as_file))

    def _setup_model(self):
        self.model_key = str(uuid.uuid4())
        self.model_contents = "model contents"
        self.model_path = os.path.join(tempfile.mkdtemp(), "mymodel")
        self.model_compute_task_key = "some compute task key"

        with open(self.model_path, "w") as f:
            f.write(self.model_contents)

        self.model_checksum = get_hash(self.model_path, self.model_compute_task_key)

    def _setup_context(self):
        self.metric_key = str(uuid.uuid4())

        class FakeContext:
            directories = self.dirs
            channel_name = CHANNEL
            compute_plan_key = "some compute plan key"
            task_category = computetask_pb2.TASK_TRAIN
            metrics = {
                self.metric_key: {
                    "key": self.metric_key,
                    "owner": "test",
                    "address": {"storage_address": "test", "checksum": "check"},
                }
            }
            algo = {
                "key": str(uuid.uuid4()),
                "owner": "test",
                "algorithm": {"storage_address": "test", "checksum": "check"},
            }

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

    @override_settings(
        ASSET_BUFFER_DIR=ASSET_BUFFER_DIR_2,
        ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS=True,
    )
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
            _add_datasamples_to_buffer(list(self.data_samples.keys())[1:])  # add samples 1 and the following ones

            for i in range(NUM_DATA_SAMPLES):
                data_sample = data_samples[i]
                dest = os.path.join(ASSET_BUFFER_DIR_2, AssetBufferDirName.Datasamples, data_sample.key)
                with open(os.path.join(dest, data_sample.filename)) as f:
                    contents = f.read()
                    self.assertEqual(contents, data_sample.contents)
                shutil.rmtree(dest)  # delete folder, otherwise next call to _add_datasamples_to_buffer will be a noop

            # Test 3: File corrupted
            data_samples[0].falsify_content("corrupted")

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
                instance = None
                mget.side_effect = lambda key: instance

                # Test 1: DB is empty
                with self.assertRaises(Exception):
                    _add_model_to_buffer(CHANNEL, model, "node 1")

                # Test 2: OK
                instance = FakeModel(File(open(self.model_path, "rb")), self.model_checksum)
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

            model["address"] = {"storage_address": storage_address, "checksum": self.model_checksum}

            with mock.patch(
                "substrapp.compute_tasks.asset_buffer.get_and_put_asset_content"
            ) as mget_and_put_asset_content:

                _add_model_to_buffer(CHANNEL, model, node_id)

                mget_and_put_asset_content.assert_called_once_with(
                    CHANNEL, storage_address, node_id, self.model_checksum, dest, self.model_compute_task_key
                )

    @override_settings(ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS=True)
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
            mget.return_value = FakeModel(File(open(self.model_path, "rb")), self.model_checksum)
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

    def test_download_metric(self):

        metrics_content = b"123"
        with mock.patch("substrapp.compute_tasks.asset_buffer.get_asset_content") as mget_asset_content:

            mget_asset_content.return_value = metrics_content

            metric = _download_metric(self.ctx, self.metric_key)
            self.assertTrue(isinstance(metric, bytes))
            self.assertEqual(metric, metrics_content)

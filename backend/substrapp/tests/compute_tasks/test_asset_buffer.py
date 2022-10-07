import os
import pathlib
import shutil
import tempfile
import uuid
from abc import ABCMeta
from abc import abstractmethod
from collections import ChainMap
from unittest import mock

import pytest
from django.core.files import File
from django.test import override_settings
from rest_framework.test import APITestCase

import orchestrator.mock as orc_mock
from orchestrator.resources import Address
from orchestrator.resources import DataManager
from substrapp import models
from substrapp.compute_tasks.asset_buffer import _add_assets_to_taskdir
from substrapp.compute_tasks.asset_buffer import _add_datasample_to_buffer
from substrapp.compute_tasks.asset_buffer import _add_model_to_buffer
from substrapp.compute_tasks.asset_buffer import _add_opener_to_buffer
from substrapp.compute_tasks.asset_buffer import init_asset_buffer
from substrapp.compute_tasks.command import Filenames
from substrapp.compute_tasks.directories import AssetBufferDirName
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.directories import init_task_dirs
from substrapp.utils import get_dir_hash
from substrapp.utils import get_hash

from ..common import FakeDataSample

ASSET_BUFFER_DIR = tempfile.mkdtemp()
ASSET_BUFFER_DIR_1 = tempfile.mkdtemp()
ASSET_BUFFER_DIR_2 = tempfile.mkdtemp()
ASSET_BUFFER_DIR_3 = tempfile.mkdtemp()
ASSET_BUFFER_DIR_4 = tempfile.mkdtemp()
CHANNEL = "mychannel"
NUM_DATA_SAMPLES = 2 * 3  # half will be registered via a path in the db, the other half by a file


class MockDataSample(metaclass=ABCMeta):
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


class MockDataSampleSavedByPath(MockDataSample):
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


class MockDataSampleSavedByFile(MockDataSample):
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
        self.data_manager = DataManager(
            key=self.data_manager_key,
            opener=Address(uri=self.opener_storage_address, checksum=self.opener_checksum),
            archived=False,
        )

    def _setup_data_samples(self):
        # half are registered in the db by a path
        self.data_samples_saved_as_path = {}
        for i in range(NUM_DATA_SAMPLES // 2):
            data_sample = MockDataSampleSavedByPath.create(i)
            self.data_samples_saved_as_path[data_sample.key] = data_sample

        # half are registered in the db by a file
        self.data_samples_saved_as_file = {}
        for i in range(int(NUM_DATA_SAMPLES / 2)):
            data_sample = MockDataSampleSavedByFile.create(i)
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
        organization_id = "organization id"

        dest = os.path.join(ASSET_BUFFER_DIR_1, AssetBufferDirName.Openers, self.data_manager_key, Filenames.Opener)

        with mock.patch("substrapp.compute_tasks.asset_buffer.organization_client.download") as mdownload, mock.patch(
            "substrapp.compute_tasks.asset_buffer.get_owner"
        ) as mget_owner:
            mget_owner.return_value = organization_id

            _add_opener_to_buffer(CHANNEL, self.data_manager)

            mdownload.assert_called_once_with(
                CHANNEL,
                organization_id,
                self.opener_storage_address,
                dest,
                self.opener_checksum,
            )

    @override_settings(
        ASSET_BUFFER_DIR=ASSET_BUFFER_DIR_2,
        ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS=True,
    )
    def test_add_datasample_to_buffer(self):

        init_asset_buffer()
        with mock.patch("substrapp.models.DataSample.objects.get") as mget:
            data_samples = list(self.data_samples.values())

            # Test 1: DB is empty
            # if the object is not present in the DB Django raise this error
            mget.side_effect = models.DataSample.DoesNotExist("datasample does not exist")
            data_sample_key = list(self.data_samples.keys())[0]
            with pytest.raises(models.DataSample.DoesNotExist) as excinfo:
                _add_datasample_to_buffer(data_sample_key)
            assert "datasample does not exist" in str(excinfo.value)

            # Test 2: OK
            mget.side_effect = lambda key: self.data_samples[key].to_fake_data_sample()

            # Add one of the data samples twice, to check that scenario
            for key in self.data_samples.keys():
                _add_datasample_to_buffer(key)

            for i in range(NUM_DATA_SAMPLES):
                data_sample = data_samples[i]
                dest = os.path.join(ASSET_BUFFER_DIR_2, AssetBufferDirName.Datasamples, data_sample.key)
                with open(os.path.join(dest, data_sample.filename)) as f:
                    contents = f.read()
                    self.assertEqual(contents, data_sample.contents)
                shutil.rmtree(dest)  # delete folder, otherwise next call to _add_datasample_to_buffer will be a noop

            # Test 3: File corrupted
            data_samples[0].falsify_content("corrupted")

            with pytest.raises(Exception) as excinfo:
                _add_datasample_to_buffer(data_samples[0].key)
            assert "checksum in tuple is not the same as in local db" in str(excinfo.value)

    @override_settings(ASSET_BUFFER_DIR=ASSET_BUFFER_DIR_3)
    def test_add_model_to_buffer(self):

        init_asset_buffer()
        dest = os.path.join(ASSET_BUFFER_DIR_3, AssetBufferDirName.Models, self.model_key)

        model = orc_mock.ModelFactory(
            key=self.model_key,
            compute_task_key=self.model_compute_task_key,
            address=Address(uri="some storage address", checksum=self.model_checksum),
        )

        organization_id = "OrgA"
        storage_address = "some storage address"

        with mock.patch("substrapp.compute_tasks.asset_buffer.organization_client.download") as mdownload:
            _add_model_to_buffer(CHANNEL, model)

            mdownload.assert_called_once_with(
                CHANNEL,
                organization_id,
                storage_address,
                dest,
                self.model_checksum,
                salt=self.model_compute_task_key,
            )

    @override_settings(ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS=True)
    def test_add_assets_to_taskdir_data_sample(self):
        data_samples = list(self.data_samples.values())

        # populate the buffer
        init_asset_buffer()
        with mock.patch("substrapp.models.DataSample.objects.get") as mget:
            mget.side_effect = lambda key: self.data_samples[key].to_fake_data_sample()
            for key in self.data_samples.keys():
                _add_datasample_to_buffer(key)

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

    @override_settings(ASSET_BUFFER_DIR=ASSET_BUFFER_DIR_4)
    def test_add_assets_to_taskdir_model(self):

        # populate the buffer
        init_asset_buffer()
        model = orc_mock.ModelFactory(
            key=self.model_key,
            compute_task_key=self.model_compute_task_key,
            address=Address(uri="some storage address", checksum=self.model_checksum),
        )

        def download_model(channel, organization_id, storage_address, dest, checksum, salt):
            shutil.copyfile(self.model_path, dest)

        with mock.patch("substrapp.compute_tasks.asset_buffer.organization_client.download") as mdownload:
            mdownload.side_effect = download_model
            _add_model_to_buffer(CHANNEL, model)

        # load from buffer into task dir
        dest = os.path.join(self.dirs.task_dir, TaskDirName.InModels, self.model_key)
        _add_assets_to_taskdir(self.dirs, AssetBufferDirName.Models, TaskDirName.InModels, [self.model_key])

        # check task dir
        with open(dest) as f:
            contents = f.read()
            self.assertEqual(contents, self.model_contents)


def test_add_assets_to_taskdir_target_directory_already_exists(settings, tmpdir):
    settings.ASSET_BUFFER_DIR = pathlib.Path(tmpdir.mkdir("asset_buffer"))

    dirs = mock.Mock()
    dirs.task_dir = pathlib.Path(tmpdir.mkdir("task_dir"))

    b_dir = "asset_buffer_datasamples"
    t_dir = "task_dir_datasamples"

    asset_keys = ["ccba50f0-a0fb-44f2-8d35-6a2bff4c6030"]

    src_dir = settings.ASSET_BUFFER_DIR / b_dir / asset_keys[0]
    src_dir.mkdir(parents=True)

    dst_dir = dirs.task_dir / t_dir / asset_keys[0]
    dst_dir.mkdir(parents=True)

    _add_assets_to_taskdir(dirs, b_dir, t_dir, keys=asset_keys)

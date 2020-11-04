import os
import shutil
import mock
import uuid
from unittest.mock import MagicMock

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from django_celery_results.models import TaskResult

from substrapp.models import DataSample
from substrapp.ledger.api import LedgerStatusError
from substrapp.utils import store_datasamples_archive
from substrapp.utils import compute_hash, get_remote_file_content, get_hash, create_directory
from substrapp.tasks.tasks import (build_subtuple_folders, get_algo, get_objective, prepare_opener,
                                   uncompress_content, prepare_data_sample, prepare_task, do_task,
                                   compute_task, remove_subtuple_materials, prepare_materials)

from .common import (get_sample_algo, get_sample_script, get_sample_zip_data_sample, get_sample_tar_data_sample,
                     get_sample_model)
from .common import FakeDataManager, FakeRequest
from . import assets
from node.models import OutgoingNode

import zipfile
MEDIA_ROOT = "/tmp/unittests_tasks/"
# MEDIA_ROOT = tempfile.mkdtemp()
CHANNEL = 'mychannel'


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(CELERY_WORKER_CONCURRENCY=1)
class TasksTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.subtuple_path = MEDIA_ROOT

        self.script, self.script_filename = get_sample_script()

        self.algo, self.algo_filename = get_sample_algo()
        self.data_sample, self.data_sample_filename = get_sample_zip_data_sample()
        self.data_sample_tar, self.data_sample_tar_filename = get_sample_tar_data_sample()
        self.model, self.model_filename = get_sample_model()

    @classmethod
    def setUpTestData(cls):
        cls.outgoing_node = OutgoingNode.objects.create(node_id="external_node_id", secret="s3cr37")
        cls.outgoing_node_traintuple = OutgoingNode.objects.create(node_id=assets.traintuple[1]['creator'],
                                                                   secret="s3cr37")
        if assets.traintuple[1]['creator'] != assets.algo[0]['owner']:
            cls.outgoing_node_algo = OutgoingNode.objects.create(node_id=assets.algo[0]['owner'], secret="s3cr37")

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_celery_retry(self):
        subtuple_key = 'test_owkin'
        subtuple = {'key': subtuple_key, 'in_models': None}

        with mock.patch('substrapp.tasks.tasks.do_task') as mdo_task,\
                mock.patch('substrapp.tasks.tasks.ComputeTask.retry') as mretry:

            mdo_task.side_effect = Exception('An exeption that should trigger retry mechanism')

            with self.assertRaises(Exception):
                compute_task(CHANNEL, 'traintuple', subtuple, None)

            self.assertEqual(mretry.call_count, 1)

    def test_create_directory(self):
        directory = './test/'
        create_directory(directory)
        self.assertTrue(os.path.exists(directory))
        remove_subtuple_materials(directory)
        self.assertFalse(os.path.exists(directory))

        # Remove a second time, it should not raise exception
        try:
            remove_subtuple_materials(directory)
        except Exception:
            self.fail('`remove_subtuple_materials` raised Exception unexpectedly!')

    def test_get_remote_file_content(self):
        content = str(self.script.read())
        checksum = compute_hash(content)
        remote_file = {'storage_address': 'localhost',
                       'checksum': checksum,
                       'owner': 'external_node_id',
                       }

        with mock.patch('substrapp.utils.get_owner') as get_owner,\
                mock.patch('substrapp.utils.requests.get') as request_get:
            get_owner.return_value = 'external_node_id'
            request_get.return_value = FakeRequest(content=content, status=status.HTTP_200_OK)

            content_remote = get_remote_file_content('mychannel', remote_file, 'external_node_id', checksum)
            self.assertEqual(content_remote, content)

        with mock.patch('substrapp.utils.get_owner') as get_owner,\
                mock.patch('substrapp.utils.requests.get') as request_get:
            get_owner.return_value = 'external_node_id'
            request_get.return_value = FakeRequest(content=content, status=status.HTTP_200_OK)

            with self.assertRaises(Exception):
                # contents (by hash) are different
                get_remote_file_content('mychannel', remote_file, 'external_node_id', 'fake_hash')

    def test_uncompress_content_tar(self):
        algo_content = self.algo.read()
        checksum = get_hash(self.algo)

        subtuple = {'key': checksum,
                    'algo': 'testalgo'}

        with mock.patch('substrapp.tasks.tasks.get_hash') as mget_hash:
            mget_hash.return_value = checksum
            uncompress_content(algo_content, os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/'))

        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/algo.py')))
        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/Dockerfile')))

    def test_uncompress_content_zip(self):
        filename = 'algo.py'
        filepath = os.path.join(self.subtuple_path, filename)
        with open(filepath, 'w') as f:
            f.write('Hello World')
        self.assertTrue(os.path.exists(filepath))

        zipname = 'sample.zip'
        zippath = os.path.join(self.subtuple_path, zipname)
        with zipfile.ZipFile(zippath, mode='w') as zf:
            zf.write(filepath, arcname=filename)
        self.assertTrue(os.path.exists(zippath))

        subtuple_key = 'testkey'
        subtuple = {'key': subtuple_key, 'algo': 'testalgo'}

        with mock.patch('substrapp.tasks.tasks.get_hash') as mget_hash:
            with open(zippath, 'rb') as content:
                mget_hash.return_value = get_hash(zippath)
                uncompress_content(content.read(), os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/'))

        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/{filename}')))

    def test_prepare_opener(self):

        filepath = os.path.join(self.subtuple_path, self.script_filename)
        with open(filepath, 'w') as f:
            f.write(self.script.read())
        self.assertTrue(os.path.exists(filepath))

        opener_checksum = get_hash(filepath)

        opener_directory = os.path.join(self.subtuple_path, 'opener')
        create_directory(opener_directory)

        with mock.patch('substrapp.models.DataManager.objects.get') as mget:
            mget.return_value = FakeDataManager(filepath)

            # test fail
            with self.assertRaises(Exception):
                prepare_opener(self.subtuple_path, {'dataset': {'opener_checksum': 'HASH'}})

            # test work
            prepare_opener(self.subtuple_path, {'dataset': {'key': 'some_key', 'opener_checksum': opener_checksum}})

            opener_path = os.path.join(opener_directory, '__init__.py')
            self.assertTrue(os.path.exists(opener_path))

            # test corrupted

            os.remove(opener_path)
            shutil.copyfile(filepath, opener_path)

            # Corrupted
            with open(opener_path, 'a+') as f:
                f.write('corrupted')

            with self.assertRaises(Exception):
                prepare_opener(self.subtuple_path, {'dataset': {'key': 'some_key', 'opener_checksum': opener_checksum}})

    def test_prepare_data_sample_zip(self):

        checksum, datasamples_path_from_file = store_datasamples_archive(self.data_sample)
        key = str(uuid.uuid4())
        data_sample = DataSample(key=key, path=datasamples_path_from_file, checksum=checksum)
        data_sample.save()

        subtuple = {
            'key': 'bar',
            'dataset': {'data_sample_keys': [str(data_sample.key)]}
        }

        with mock.patch('substrapp.models.DataSample.objects.get') as mget:
            mget.return_value = data_sample

            subtuple_directory = build_subtuple_folders(subtuple)

            prepare_data_sample(subtuple_directory, subtuple)

            # check folder has been correctly renamed with key of directory containing uncompressed data sample
            self.assertFalse(
                os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', 'foo')))
            self.assertTrue(
                os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', key)))

            # check subtuple folder has been created and sym links exists
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.key)))
            self.assertTrue(os.path.islink(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.key)))
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.key, 'LABEL_0024900.csv')))
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.key, 'IMG_0024900.jpg')))

    def test_prepare_data_sample_zip_fail(self):

        data_sample = DataSample(key=uuid.uuid4(), path=self.data_sample_filename)
        data_sample.save()

        subtuple = {
            'key': 'bar',
            'dataset': {'data_sample_keys': ['fake_pk']}
        }

        subtuple2 = {
            'key': 'bar',
            'dataset': {'data_sample_keys': [data_sample.key]}
        }

        with mock.patch('substrapp.models.DataSample.objects.get') as mget:
            mget.return_value = data_sample

            subtuple_directory = build_subtuple_folders(subtuple)

            with self.assertRaises(Exception):
                prepare_data_sample(subtuple_directory, subtuple)

            with self.assertRaises(Exception):
                prepare_data_sample('/fake/directory/failure', subtuple2)

    def test_put_data_tar(self):

        checksum, datasamples_path_from_file = store_datasamples_archive(self.data_sample_tar)

        key = str(uuid.uuid4())
        data_sample = DataSample(key=key, path=datasamples_path_from_file, checksum=checksum)
        data_sample.save()

        subtuple = {
            'key': 'bar',
            'dataset': {'data_sample_keys': [str(data_sample.key)]}
        }

        with mock.patch('substrapp.models.DataSample.objects.get') as mget:
            mget.return_value = data_sample

            subtuple_directory = build_subtuple_folders(subtuple)

            prepare_data_sample(subtuple_directory, subtuple)

            # check folder has been correctly renamed with key of directory containing uncompressed data_sample
            self.assertFalse(os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', 'foo')))
            self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', key)))

            # check subtuple folder has been created and sym links exists
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.key)))
            self.assertTrue(os.path.islink(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.key)))
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.key, 'LABEL_0024900.csv')))
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.key, 'IMG_0024900.jpg')))

    def test_get_algo(self):
        algo_content = self.algo.read()
        algo_checksum = get_hash(self.algo)

        subtuple = {
            'algo': {
                'key': assets.algo[0]['key'],
                'storage_address': assets.algo[0]['content']['storage_address'],
                'owner': assets.algo[0]['owner'],
                'checksum': algo_checksum
            }
        }

        with mock.patch('substrapp.tasks.utils.get_remote_file_content') as mget_remote_file,\
                mock.patch('substrapp.tasks.utils.get_owner') as get_owner,\
                mock.patch('substrapp.tasks.tasks.get_object_from_ledger') as get_object_from_ledger:
            mget_remote_file.return_value = algo_content
            get_owner.return_value = 'external_node_id'
            get_object_from_ledger.return_value = assets.algo[0]

            data = get_algo(CHANNEL, 'traintuple', subtuple)
            self.assertEqual(algo_content, data)

    def test_get_objective(self):
        metrics_content = self.script.read().encode('utf-8')
        objective_key = uuid.uuid4()

        with mock.patch('substrapp.tasks.utils.get_remote_file_content') as mget_remote_file, \
                mock.patch('substrapp.tasks.tasks.get_object_from_ledger'), \
                mock.patch('substrapp.tasks.utils.authenticate_worker'):

            mget_remote_file.return_value = metrics_content

            objective = get_objective(CHANNEL, {'objective': {'key': objective_key,
                                                'metrics': ''}})
            self.assertTrue(isinstance(objective, bytes))
            self.assertEqual(objective, metrics_content)

    def test_build_subtuple_folders(self):
        with mock.patch('substrapp.tasks.tasks.getattr') as getattr:
            getattr.return_value = self.subtuple_path

            subtuple_key = 'test1234'
            subtuple = {'key': subtuple_key}
            subtuple_directory = build_subtuple_folders(subtuple)

            self.assertTrue(os.path.exists(subtuple_directory))
            self.assertEqual(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}'), subtuple_directory)

            for root, dirs, files in os.walk(subtuple_directory):
                nb_subfolders = len(dirs)

            self.assertTrue(5, nb_subfolders)

    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory'
    )
    def test_prepare_tasks(self):

        class FakeSettings(object):
            def __init__(self):
                self.MEDIA_ROOT = MEDIA_ROOT

        subtuple = [{'key': 'subtuple_test', 'compute_plan_key': 'flkey', 'status': 'todo'}]

        with mock.patch('substrapp.tasks.tasks.settings') as msettings, \
                mock.patch.object(TaskResult.objects, 'filter') as mtaskresult, \
                mock.patch('substrapp.tasks.tasks.get_hash') as mget_hash, \
                mock.patch('substrapp.tasks.tasks.query_tuples') as mquery_tuples, \
                mock.patch('substrapp.tasks.tasks.get_objective') as mget_objective, \
                mock.patch('substrapp.tasks.tasks.get_algo') as mget_algo, \
                mock.patch('substrapp.tasks.tasks.prepare_models'), \
                mock.patch('substrapp.tasks.tasks.build_subtuple_folders') as mbuild_subtuple_folders, \
                mock.patch('substrapp.tasks.tasks.prepare_opener') as mprepare_opener, \
                mock.patch('substrapp.tasks.tasks.prepare_data_sample') as mprepare_data_sample, \
                mock.patch('substrapp.tasks.tasks.uncompress_content'), \
                mock.patch('substrapp.tasks.tasks.json.loads') as mjson_loads, \
                mock.patch('substrapp.tasks.tasks.AsyncResult') as masyncres, \
                mock.patch('substrapp.tasks.tasks.get_owner') as get_owner,\
                mock.patch('substrapp.tasks.tasks.find_training_step_tuple_from_key') as gettuple:

            msettings.return_value = FakeSettings()
            mget_hash.return_value = 'owkinhash'
            mquery_tuples.return_value = subtuple
            mget_objective.return_value = 'objective'
            mget_algo.return_value = 'algo', 'algo_key'
            mbuild_subtuple_folders.return_value = MEDIA_ROOT
            mprepare_opener.return_value = 'opener'
            mprepare_data_sample.return_value = 'data'
            get_owner.return_value = 'foo'
            gettuple.return_value = None, subtuple[0]

            masyncres.return_value.state = 'PENDING'

            mock_filter = MagicMock()
            mock_filter.count.return_value = 1
            mtaskresult.return_value = mock_filter

            mjson_loads.return_value = {'worker': 'worker'}

            with mock.patch('substrapp.tasks.tasks.log_start_tuple') as mlog_start_tuple:
                mlog_start_tuple.side_effect = LedgerStatusError('Bad Response')
                prepare_task(CHANNEL, 'traintuple')

            with mock.patch('substrapp.tasks.tasks.log_start_tuple') as mlog_start_tuple, \
                    mock.patch('substrapp.tasks.tasks.compute_task.apply_async') as mapply_async:
                mlog_start_tuple.return_value = 'data', 201
                mapply_async.return_value = 'do_task'
                prepare_task(CHANNEL, 'traintuple')

    def test_do_task(self):

        class FakeSettings(object):
            def __init__(self):
                self.MEDIA_ROOT = MEDIA_ROOT

        subtuple_key = 'test_owkin'
        subtuple = {'key': subtuple_key, 'in_models': None, 'algo': {'key': 'mykey', 'checksum': 'myhash'}}
        subtuple_directory = build_subtuple_folders(subtuple)

        with mock.patch('substrapp.tasks.tasks.settings') as msettings, \
                mock.patch('substrapp.tasks.tasks.getattr') as mgetattr:
            msettings.return_value = FakeSettings()
            mgetattr.return_value = self.subtuple_path

            for name in ['opener', 'metrics']:
                with open(os.path.join(subtuple_directory, f'{name}/{name}.py'), 'w') as f:
                    f.write('Hello World')

            perf = 0.3141592
            with open(os.path.join(subtuple_directory, 'pred/perf.json'), 'w') as f:
                f.write(f'{{"all": {perf}}}')

            with open(os.path.join(subtuple_directory, 'output_model/model'), 'w') as f:
                f.write("MODEL")

            with mock.patch('substrapp.tasks.tasks.compute_job') as mcompute_job:
                mcompute_job.return_value = 'DONE'
                do_task(CHANNEL, subtuple, 'traintuple')

    def test_compute_task(self):

        subtuple_key = 'test_owkin'
        subtuple = {'key': subtuple_key, 'in_models': None}
        subtuple_directory = build_subtuple_folders(subtuple)

        with mock.patch('substrapp.tasks.tasks.log_start_tuple') as mlog_start_tuple:
            mlog_start_tuple.return_value = 'data', 200

            for name in ['opener', 'metrics']:
                with open(os.path.join(subtuple_directory, f'{name}/{name}.py'), 'w') as f:
                    f.write('Hello World')

            perf = 0.3141592
            with open(os.path.join(subtuple_directory, 'pred/perf.json'), 'w') as f:
                f.write(f'{{"all": {perf}}}')

            with open(os.path.join(subtuple_directory, 'model/model'), 'w') as f:
                f.write("MODEL")

            with mock.patch('substrapp.tasks.tasks.compute_job') as mcompute_job, \
                    mock.patch('substrapp.tasks.tasks.do_task') as mdo_task,\
                    mock.patch('substrapp.tasks.tasks.prepare_materials') as mprepare_materials, \
                    mock.patch('substrapp.tasks.tasks.log_success_tuple') as mlog_success_tuple:

                mcompute_job.return_value = 'DONE'
                mprepare_materials.return_value = 'DONE'
                mdo_task.return_value = 'DONE'

                mlog_success_tuple.return_value = 'data', 201
                compute_task(CHANNEL, 'traintuple', subtuple, None)

                mlog_success_tuple.return_value = 'data', 404
                compute_task(CHANNEL, 'traintuple', subtuple, None)

                with mock.patch('substrapp.tasks.tasks.log_fail_tuple') as mlog_fail_tuple:
                    mdo_task.side_effect = Exception("Test")
                    mlog_fail_tuple.return_value = 'data', 404
                    with self.assertRaises(Exception) as exc:
                        compute_task(CHANNEL, 'traintuple', subtuple, None)
                    self.assertEqual(str(exc.exception), "Test")

    def test_prepare_materials(self):

        class FakeSettings(object):
            def __init__(self):
                self.MEDIA_ROOT = MEDIA_ROOT

        subtuple = [{
            'key': 'subtuple_test',
            'compute_plan_key': 'flkey',
            'traintuple_key': 'subtuple_test',
            'traintuple_type': 'traintuple'
        }]

        with mock.patch('substrapp.tasks.tasks.settings') as msettings, \
                mock.patch('substrapp.tasks.tasks.get_hash') as mget_hash, \
                mock.patch('substrapp.tasks.tasks.query_tuples') as mquery_tuples, \
                mock.patch('substrapp.tasks.tasks.get_objective') as mget_objective, \
                mock.patch('substrapp.tasks.tasks.get_algo') as mget_algo, \
                mock.patch('substrapp.tasks.tasks.prepare_models'), \
                mock.patch('substrapp.tasks.tasks.build_subtuple_folders') as mbuild_subtuple_folders, \
                mock.patch('substrapp.tasks.tasks.prepare_opener'), \
                mock.patch('substrapp.tasks.tasks.prepare_data_sample'), \
                mock.patch('substrapp.tasks.tasks.uncompress_content'):

            msettings.return_value = FakeSettings()
            mget_hash.return_value = 'owkinhash'
            mquery_tuples.return_value = subtuple, 200
            mget_objective.return_value = 'objective'
            mget_algo.return_value = 'algo', 'algo_key'
            mbuild_subtuple_folders.return_value = MEDIA_ROOT

            prepare_materials(CHANNEL, subtuple[0], 'traintuple')
            prepare_materials(CHANNEL, subtuple[0], 'testtuple')

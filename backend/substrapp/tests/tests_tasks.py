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
from substrapp.ledger_utils import LedgerStatusError
from substrapp.utils import store_datasamples_archive
from substrapp.utils import compute_hash, get_remote_file_content, get_hash, create_directory
from substrapp.tasks.utils import ResourcesManager, compute_docker
from substrapp.tasks.tasks import (build_subtuple_folders, get_algo, get_model, get_models, get_objective, put_opener,
                                   put_model, put_models, put_algo, put_metric, put_data_sample, prepare_task, do_task,
                                   compute_task, remove_subtuple_materials, prepare_materials)

from .common import (get_sample_algo, get_sample_script, get_sample_zip_data_sample, get_sample_tar_data_sample,
                     get_sample_model)
from .common import FakeObjective, FakeDataManager, FakeModel, FakeRequest
from . import assets
from node.models import OutgoingNode

import zipfile
import docker
MEDIA_ROOT = "/tmp/unittests_tasks/"
# MEDIA_ROOT = tempfile.mkdtemp()


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
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

        self.ResourcesManager = ResourcesManager()

    @classmethod
    def setUpTestData(cls):
        cls.outgoing_node = OutgoingNode.objects.create(node_id="external_node_id", secret="s3cr37")
        cls.outgoing_node_traintuple = OutgoingNode.objects.create(node_id=assets.traintuple[1]['creator'],
                                                                   secret="s3cr37")
        if assets.traintuple[1]['creator'] != assets.algo[0]['owner']:
            cls.outgoing_node_algo = OutgoingNode.objects.create(node_id=assets.algo[0]['owner'], secret="s3cr37")

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

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
        pkhash = compute_hash(content)
        remote_file = {'storageAddress': 'localhost',
                       'hash': pkhash,
                       'owner': 'external_node_id',
                       }

        with mock.patch('substrapp.utils.get_owner') as get_owner,\
                mock.patch('substrapp.utils.requests.get') as request_get:
            get_owner.return_value = 'external_node_id'
            request_get.return_value = FakeRequest(content=content, status=status.HTTP_200_OK)

            content_remote = get_remote_file_content(remote_file, 'external_node_id', pkhash)
            self.assertEqual(content_remote, content)

        with mock.patch('substrapp.utils.get_owner') as get_owner,\
                mock.patch('substrapp.utils.requests.get') as request_get:
            get_owner.return_value = 'external_node_id'
            request_get.return_value = FakeRequest(content=content, status=status.HTTP_200_OK)

            with self.assertRaises(Exception):
                # contents (by pkhash) are different
                get_remote_file_content(remote_file, 'external_node_id', 'fake_pkhash')

    def test_Ressource_Manager(self):

        self.assertTrue(isinstance(self.ResourcesManager.memory_limit_mb(), int))

        cpu_set, gpu_set = self.ResourcesManager.get_cpu_gpu_sets()
        self.assertIn(cpu_set, self.ResourcesManager._ResourcesManager__cpu_sets)

        if gpu_set is not None:
            self.assertIn(gpu_set, self.ResourcesManager._ResourcesManager__gpu_sets)

    def test_put_algo_tar(self):
        algo_content = self.algo.read()
        subtuple_key = get_hash(self.algo)

        subtuple = {'key': subtuple_key,
                    'algo': 'testalgo'}

        with mock.patch('substrapp.tasks.tasks.get_hash') as mget_hash:
            mget_hash.return_value = subtuple_key
            put_algo(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/'), algo_content)

        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/algo.py')))
        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/Dockerfile')))

    def test_put_algo_zip(self):
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
                put_algo(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/'), content.read())

        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/{filename}')))

    def test_put_metric(self):
        filename = 'metrics.py'
        filepath = os.path.join(self.subtuple_path, filename)
        with open(filepath, 'w') as f:
            f.write('Hello World')
        self.assertTrue(os.path.exists(filepath))

        zipname = 'sample.zip'
        zippath = os.path.join(self.subtuple_path, zipname)
        with zipfile.ZipFile(zippath, mode='w') as zf:
            zf.write(filepath, arcname=filename)
        self.assertTrue(os.path.exists(zippath))

        metrics_directory = os.path.join(self.subtuple_path)
        create_directory(metrics_directory)

        with mock.patch('substrapp.tasks.tasks.get_hash') as mget_hash:
            with open(zippath, 'rb') as content:
                mget_hash.return_value = 'hash_value'
                put_metric(metrics_directory, content.read())

        self.assertTrue(os.path.exists(os.path.join(metrics_directory, 'metrics.py')))

    def test_put_opener(self):

        filepath = os.path.join(self.subtuple_path, self.script_filename)
        with open(filepath, 'w') as f:
            f.write(self.script.read())
        self.assertTrue(os.path.exists(filepath))

        opener_hash = get_hash(filepath)

        opener_directory = os.path.join(self.subtuple_path, 'opener')
        create_directory(opener_directory)

        with mock.patch('substrapp.models.DataManager.objects.get') as mget:
            mget.return_value = FakeDataManager(filepath)

            # test fail
            with self.assertRaises(Exception):
                put_opener({'dataset': {'openerHash': 'HASH'}}, self.subtuple_path)

            # test work
            put_opener({'dataset': {'openerHash': opener_hash}}, self.subtuple_path)

            opener_path = os.path.join(opener_directory, 'opener.py')
            self.assertTrue(os.path.exists(opener_path))

            # test corrupted

            os.remove(opener_path)
            shutil.copyfile(filepath, opener_path)

            # Corrupted
            with open(opener_path, 'a+') as f:
                f.write('corrupted')

            with self.assertRaises(Exception):
                put_opener({'dataset': {'openerHash': opener_hash}}, self.subtuple_path)

    def test_put_data_sample_zip(self):

        dir_pkhash, datasamples_path_from_file = store_datasamples_archive(self.data_sample)

        data_sample = DataSample(pkhash=dir_pkhash, path=datasamples_path_from_file)
        data_sample.save()

        subtuple = {
            'key': 'bar',
            'dataset': {'keys': [data_sample.pk]}
        }

        with mock.patch('substrapp.models.DataSample.objects.get') as mget:
            mget.return_value = data_sample

            subtuple_directory = build_subtuple_folders(subtuple)

            put_data_sample(subtuple, subtuple_directory)

            # check folder has been correctly renamed with pk of directory containing uncompressed data sample
            self.assertFalse(
                os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', 'foo')))
            self.assertTrue(
                os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', dir_pkhash)))

            # check subtuple folder has been created and sym links exists
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk)))
            self.assertTrue(os.path.islink(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk)))
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk, 'LABEL_0024900.csv')))
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk, 'IMG_0024900.jpg')))

    def test_put_data_sample_zip_fail(self):

        data_sample = DataSample(pkhash='foo', path=self.data_sample)
        data_sample.save()

        subtuple = {
            'key': 'bar',
            'dataset': {'keys': ['fake_pk']}
        }

        subtuple2 = {
            'key': 'bar',
            'dataset': {'keys': [data_sample.pk]}
        }

        with mock.patch('substrapp.models.DataSample.objects.get') as mget:
            mget.return_value = data_sample

            subtuple_directory = build_subtuple_folders(subtuple)

            with self.assertRaises(Exception):
                put_data_sample(subtuple, subtuple_directory)

            with self.assertRaises(Exception):
                put_data_sample(subtuple2, '/fake/directory/failure')

    def test_put_data_tar(self):

        dir_pkhash, datasamples_path_from_file = store_datasamples_archive(self.data_sample_tar)

        data_sample = DataSample(pkhash=dir_pkhash, path=datasamples_path_from_file)
        data_sample.save()

        subtuple = {
            'key': 'bar',
            'dataset': {'keys': [data_sample.pk]}
        }

        with mock.patch('substrapp.models.DataSample.objects.get') as mget:
            mget.return_value = data_sample

            subtuple_directory = build_subtuple_folders(subtuple)

            put_data_sample(subtuple, subtuple_directory)

            # check folder has been correctly renamed with pk of directory containing uncompressed data_sample
            self.assertFalse(os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', 'foo')))
            self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', dir_pkhash)))

            # check subtuple folder has been created and sym links exists
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk)))
            self.assertTrue(os.path.islink(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk)))
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk, 'LABEL_0024900.csv')))
            self.assertTrue(os.path.exists(os.path.join(
                MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk, 'IMG_0024900.jpg')))

    def test_put_model(self):

        model_content = self.model.read().encode()

        traintupleKey = compute_hash(model_content)
        model_hash = compute_hash(model_content, traintupleKey)
        subtuple = {'key': model_hash, 'traintupleKey': traintupleKey}

        model_directory = os.path.join(self.subtuple_path, 'model')
        create_directory(model_directory)
        put_model(subtuple, self.subtuple_path, model_content, model_hash)

        model_path = os.path.join(model_directory, traintupleKey)
        self.assertTrue(os.path.exists(model_path))

        shutil.copyfile(model_path, model_path + '-local')

        # Corrupted
        with open(model_path, 'a+') as f:
            f.write('corrupted')

        with mock.patch('substrapp.models.Model.objects.get') as mget:
            mget.return_value = FakeModel(model_path + '-local')
            with self.assertRaises(Exception):
                put_model({'traintupleKey': traintupleKey, 'traintupleType': 'traintuple'},
                          self.subtuple_path, model_content, model_hash)

        os.remove(model_path)

        with mock.patch('substrapp.models.Model.objects.get') as mget:
            mget.return_value = FakeModel(model_path + '-local')
            put_model(subtuple, self.subtuple_path, model_content, model_hash)
            self.assertTrue(os.path.exists(model_path))

        with mock.patch('substrapp.models.Model.objects.get') as mget:
            mget.return_value = FakeModel(model_path)
            with self.assertRaises(Exception):
                put_model({'traintupleKey': traintupleKey, 'traintupleType': 'traintuple'},
                          self.subtuple_path, model_content, 'fail-hash')

        with self.assertRaises(Exception):
            put_model(subtuple, self.subtuple_path, None, None)

    def test_put_models(self):

        model_content = self.model.read().encode()
        models_content = [model_content, model_content + b', -2.0']

        traintupleKey = compute_hash(models_content[0])
        model_hash = compute_hash(models_content[0], traintupleKey)

        traintupleKey2 = compute_hash(models_content[1])
        model_hash2 = compute_hash(models_content[1], traintupleKey2)

        model_path = os.path.join(self.subtuple_path, 'model', traintupleKey)
        model_path2 = os.path.join(self.subtuple_path, 'model', traintupleKey2)

        model_type = 'inModels'
        subtuple = {model_type: [{'hash': model_hash, 'traintupleKey': traintupleKey, 'traintupleType': 'traintuple'},
                                 {'hash': model_hash2, 'traintupleKey': traintupleKey2,
                                  'traintupleType': 'traintuple'}]}

        model_directory = os.path.join(self.subtuple_path, 'model/')

        create_directory(model_directory)
        put_models(subtuple, self.subtuple_path, models_content)

        self.assertTrue(os.path.exists(model_path))
        self.assertTrue(os.path.exists(model_path2))

        os.rename(model_path, model_path + '-local')
        os.rename(model_path2, model_path2 + '-local')

        with mock.patch('substrapp.models.Model.objects.get') as mget:
            mget.side_effect = [FakeModel(model_path + '-local'), FakeModel(model_path2 + '-local')]
            put_models(subtuple, self.subtuple_path, models_content)

            self.assertTrue(os.path.exists(model_path))
            self.assertTrue(os.path.exists(model_path2))

        with mock.patch('substrapp.models.Model.objects.get') as mget:
            mget.return_value = FakeModel(model_path)
            with self.assertRaises(Exception):
                put_models({'inModels': [{'hash': 'hash'}]}, self.subtuple_path, model_content)

        with self.assertRaises(Exception):
            put_models({'model': {'hash': 'fail-hash'}}, self.subtuple_path, None)

    def test_get_model(self):
        model_content = self.model.read().encode()
        traintupleKey = compute_hash(model_content)
        subtuple = {'traintupleKey': traintupleKey}

        with mock.patch('substrapp.tasks.utils.get_remote_file_content') as mget_remote_file, \
                mock.patch('substrapp.tasks.utils.get_owner') as mget_owner,\
                mock.patch('substrapp.tasks.tasks.get_object_from_ledger') as mget_object_from_ledger:
            mget_remote_file.return_value = model_content
            mget_owner.return_value = assets.traintuple[2]['creator']
            mget_object_from_ledger.return_value = assets.traintuple[2]  # uses index 1 to have a set value of outModel
            model_content = get_model(subtuple)

        self.assertIsNotNone(model_content)

        self.assertIsNone(get_model({}))

    def test_get_models(self):
        model_content = self.model.read().encode()
        models_content = [model_content, model_content + b', -2.0']

        traintupleKey = compute_hash(models_content[0])
        model_hash = compute_hash(models_content[0], traintupleKey)

        traintupleKey2 = compute_hash(models_content[1])
        model_hash2 = compute_hash(models_content[1], traintupleKey2)

        model_type = 'inModels'
        subtuple = {model_type: [
            {'hash': model_hash, 'traintupleKey': traintupleKey, 'traintupleType': 'traintuple'},
            {'hash': model_hash2, 'traintupleKey': traintupleKey2, 'traintupleType': 'traintuple'}]
        }

        with mock.patch('substrapp.tasks.utils.get_remote_file_content') as mget_remote_file, \
                mock.patch('substrapp.tasks.utils.authenticate_worker'),\
                mock.patch('substrapp.tasks.tasks.get_object_from_ledger'):
            mget_remote_file.side_effect = (models_content[0], models_content[1])
            models_content_res = get_models(subtuple)

        self.assertEqual(models_content_res, models_content)

        self.assertEqual(len(get_models({})), 0)

    def test_get_algo(self):
        algo_content = self.algo.read()
        algo_hash = get_hash(self.algo)

        subtuple = {
            'algo': {
                'storageAddress': assets.algo[0]['content']['storageAddress'],
                'owner': assets.algo[0]['owner'],
                'hash': algo_hash
            }
        }

        with mock.patch('substrapp.tasks.utils.get_remote_file_content') as mget_remote_file,\
                mock.patch('substrapp.tasks.utils.get_owner') as get_owner,\
                mock.patch('substrapp.tasks.tasks.get_object_from_ledger') as get_object_from_ledger:
            mget_remote_file.return_value = algo_content
            get_owner.return_value = 'external_node_id'
            get_object_from_ledger.return_value = assets.algo[0]

            data = get_algo(subtuple)
            self.assertEqual(algo_content, data)

    def test_get_objective(self):
        metrics_content = self.script.read().encode('utf-8')
        objective_hash = get_hash(self.script)

        with mock.patch('substrapp.models.Objective.objects.get') as mget:

            mget.return_value = FakeObjective()

            objective = get_objective({'objective': {'hash': objective_hash,
                                                     'metrics': ''}})
            self.assertTrue(isinstance(objective, bytes))
            self.assertEqual(objective, b'foo')

        with mock.patch('substrapp.tasks.utils.get_remote_file_content') as mget_remote_file, \
                mock.patch('substrapp.tasks.tasks.get_object_from_ledger'), \
                mock.patch('substrapp.tasks.utils.authenticate_worker'),\
                mock.patch('substrapp.models.Objective.objects.update_or_create') as mupdate_or_create:

            mget.return_value = FakeObjective()
            mget_remote_file.return_value = metrics_content
            mupdate_or_create.return_value = FakeObjective(), True

            objective = get_objective({'objective': {'hash': objective_hash,
                                                     'metrics': ''}})
            self.assertTrue(isinstance(objective, bytes))
            self.assertEqual(objective, b'foo')

    def test_compute_docker(self):
        cpu_set, gpu_set = None, None
        client = docker.from_env()

        dockerfile_path = os.path.join(self.subtuple_path, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write('FROM library/hello-world')

        hash_docker = uuid.uuid4().hex
        compute_docker(client, self.ResourcesManager,
                       self.subtuple_path, 'test_compute_docker_' + hash_docker,
                       'test_compute_docker_name_' + hash_docker, None, None)

        self.assertIsNone(cpu_set)
        self.assertIsNone(gpu_set)

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
                self.LEDGER = {'signcert': 'signcert',
                               'org': 'owkin',
                               'peer': 'peer'}

                self.MEDIA_ROOT = MEDIA_ROOT

        subtuple = [{'key': 'subtuple_test', 'computePlanID': 'flkey'}]

        with mock.patch('substrapp.tasks.tasks.settings') as msettings, \
                mock.patch.object(TaskResult.objects, 'filter') as mtaskresult, \
                mock.patch('substrapp.tasks.tasks.get_hash') as mget_hash, \
                mock.patch('substrapp.tasks.tasks.query_tuples') as mquery_tuples, \
                mock.patch('substrapp.tasks.tasks.get_objective') as mget_objective, \
                mock.patch('substrapp.tasks.tasks.get_algo') as mget_algo, \
                mock.patch('substrapp.tasks.tasks.get_model') as mget_model, \
                mock.patch('substrapp.tasks.tasks.build_subtuple_folders') as mbuild_subtuple_folders, \
                mock.patch('substrapp.tasks.tasks.put_opener') as mput_opener, \
                mock.patch('substrapp.tasks.tasks.put_data_sample') as mput_data_sample, \
                mock.patch('substrapp.tasks.tasks.put_metric') as mput_metric, \
                mock.patch('substrapp.tasks.tasks.put_algo') as mput_algo, \
                mock.patch('substrapp.tasks.tasks.json.loads') as mjson_loads, \
                mock.patch('substrapp.tasks.tasks.AsyncResult') as masyncres, \
                mock.patch('substrapp.tasks.tasks.put_model') as mput_model, \
                mock.patch('substrapp.tasks.tasks.get_owner') as get_owner:

            msettings.return_value = FakeSettings()
            mget_hash.return_value = 'owkinhash'
            mquery_tuples.return_value = subtuple
            mget_objective.return_value = 'objective'
            mget_algo.return_value = 'algo', 'algo_hash'
            mget_model.return_value = 'model', 'model_hash'
            mbuild_subtuple_folders.return_value = MEDIA_ROOT
            mput_opener.return_value = 'opener'
            mput_data_sample.return_value = 'data'
            mput_metric.return_value = 'metric'
            mput_algo.return_value = 'algo'
            mput_model.return_value = 'model'
            get_owner.return_value = 'foo'

            masyncres.return_value.state = 'PENDING'

            mock_filter = MagicMock()
            mock_filter.count.return_value = 1
            mtaskresult.return_value = mock_filter

            mjson_loads.return_value = {'worker': 'worker'}

            with mock.patch('substrapp.tasks.tasks.log_start_tuple') as mlog_start_tuple:
                mlog_start_tuple.side_effect = LedgerStatusError('Bad Response')
                prepare_task('traintuple')

            with mock.patch('substrapp.tasks.tasks.log_start_tuple') as mlog_start_tuple, \
                    mock.patch('substrapp.tasks.tasks.compute_task.apply_async') as mapply_async:
                mlog_start_tuple.return_value = 'data', 201
                mapply_async.return_value = 'do_task'
                prepare_task('traintuple')

    def test_do_task(self):

        class FakeSettings(object):
            def __init__(self):
                self.LEDGER = {'signcert': 'signcert',
                               'org': 'owkin',
                               'peer': 'peer'}

                self.MEDIA_ROOT = MEDIA_ROOT

        subtuple_key = 'test_owkin'
        subtuple = {'key': subtuple_key, 'inModels': None}
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

            with open(os.path.join(subtuple_directory, 'model/model'), 'w') as f:
                f.write("MODEL")

            with mock.patch('substrapp.tasks.tasks.compute_docker') as mcompute_docker:
                mcompute_docker.return_value = 'DONE'
                do_task(subtuple, 'traintuple')

    def test_compute_task(self):

        class FakeSettings(object):
            def __init__(self):
                self.LEDGER = {'signcert': 'signcert',
                               'org': 'owkin',
                               'peer': 'peer'}

                self.MEDIA_ROOT = MEDIA_ROOT

        subtuple_key = 'test_owkin'
        subtuple = {'key': subtuple_key, 'inModels': None}
        subtuple_directory = build_subtuple_folders(subtuple)

        with mock.patch('substrapp.tasks.tasks.settings') as msettings, \
                mock.patch('substrapp.tasks.tasks.getattr') as mgetattr, \
                mock.patch('substrapp.tasks.tasks.log_start_tuple') as mlog_start_tuple:
            msettings.return_value = FakeSettings()
            mgetattr.return_value = self.subtuple_path
            mlog_start_tuple.return_value = 'data', 200

            for name in ['opener', 'metrics']:
                with open(os.path.join(subtuple_directory, f'{name}/{name}.py'), 'w') as f:
                    f.write('Hello World')

            perf = 0.3141592
            with open(os.path.join(subtuple_directory, 'pred/perf.json'), 'w') as f:
                f.write(f'{{"all": {perf}}}')

            with open(os.path.join(subtuple_directory, 'model/model'), 'w') as f:
                f.write("MODEL")

            with mock.patch('substrapp.tasks.tasks.compute_docker') as mcompute_docker, \
                    mock.patch('substrapp.tasks.tasks.do_task') as mdo_task,\
                    mock.patch('substrapp.tasks.tasks.prepare_materials') as mprepare_materials, \
                    mock.patch('substrapp.tasks.tasks.log_success_tuple') as mlog_success_tuple:

                mcompute_docker.return_value = 'DONE'
                mprepare_materials.return_value = 'DONE'
                mdo_task.return_value = 'DONE'

                mlog_success_tuple.return_value = 'data', 201
                compute_task('traintuple', subtuple, None)

                mlog_success_tuple.return_value = 'data', 404
                compute_task('traintuple', subtuple, None)

                with mock.patch('substrapp.tasks.tasks.log_fail_tuple') as mlog_fail_tuple:
                    mdo_task.side_effect = Exception("Test")
                    mlog_fail_tuple.return_value = 'data', 404
                    compute_task('traintuple', subtuple, None)

    def test_prepare_materials(self):

        class FakeSettings(object):
            def __init__(self):
                self.LEDGER = {'signcert': 'signcert',
                               'org': 'owkin',
                               'peer': 'peer'}

                self.MEDIA_ROOT = MEDIA_ROOT

        subtuple = [{
            'key': 'subtuple_test',
            'computePlanID': 'flkey',
            'traintupleKey': 'subtuple_test',
            'traintupleType': 'traintuple'
        }]

        with mock.patch('substrapp.tasks.tasks.settings') as msettings, \
                mock.patch('substrapp.tasks.tasks.get_hash') as mget_hash, \
                mock.patch('substrapp.tasks.tasks.query_tuples') as mquery_tuples, \
                mock.patch('substrapp.tasks.tasks.get_objective') as mget_objective, \
                mock.patch('substrapp.tasks.tasks.get_algo') as mget_algo, \
                mock.patch('substrapp.tasks.tasks.get_model') as mget_model, \
                mock.patch('substrapp.tasks.tasks.get_traintuple_metadata') as mget_traintuple_metadata, \
                mock.patch('substrapp.tasks.tasks.build_subtuple_folders') as mbuild_subtuple_folders, \
                mock.patch('substrapp.tasks.tasks.put_opener') as mput_opener, \
                mock.patch('substrapp.tasks.tasks.put_data_sample') as mput_data_sample, \
                mock.patch('substrapp.tasks.tasks.put_metric') as mput_metric, \
                mock.patch('substrapp.tasks.tasks.put_algo') as mput_algo, \
                mock.patch('substrapp.tasks.tasks.put_model') as mput_model:

            msettings.return_value = FakeSettings()
            mget_hash.return_value = 'owkinhash'
            mquery_tuples.return_value = subtuple, 200
            mget_objective.return_value = 'objective'
            mget_algo.return_value = 'algo', 'algo_hash'
            mget_model.return_value = 'model', 'model_hash'
            mget_traintuple_metadata.return_value = {'outModel': {'hash': 'model_hash'}}
            mbuild_subtuple_folders.return_value = MEDIA_ROOT
            mput_opener.return_value = 'opener'
            mput_data_sample.return_value = 'data'
            mput_metric.return_value = 'metric'
            mput_algo.return_value = 'algo'
            mput_model.return_value = 'model'

            prepare_materials(subtuple[0], 'traintuple')
            prepare_materials(subtuple[0], 'testtuple')

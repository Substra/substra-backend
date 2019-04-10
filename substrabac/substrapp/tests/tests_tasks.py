import os
import shutil
import mock
import time

from django.test import override_settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.models import DataSample
from substrapp.utils import compute_hash, get_computed_hash, get_remote_file, get_hash, create_directory
from substrapp.task_utils import ResourcesManager, monitoring_task, compute_docker, ExceptionThread
from substrapp.tasks import build_subtuple_folders, get_algo, get_model, get_models, get_objective, put_opener, put_model, put_models, put_algo, put_metric, put_data_sample, prepareTask, doTask, computeTask

from .common import get_sample_algo, get_sample_script, get_sample_zip_data_sample, get_sample_tar_data_sample, get_sample_model
from .common import FakeClient, FakeObjective, FakeDataManager, FakeModel

import zipfile
import docker
MEDIA_ROOT = "/tmp/unittests_tasks/"
# MEDIA_ROOT = tempfile.mkdtemp()


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
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

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_create_directory(self):
        directory = './test/'
        create_directory(directory)
        self.assertTrue(os.path.exists(directory))
        shutil.rmtree(directory)

    def test_get_computed_hash(self):
        with mock.patch('substrapp.utils.requests.get') as mget:
            mget.return_value = HttpResponse(str(self.script.read()))
            _, pkhash = get_computed_hash('localhost')
            self.assertEqual(pkhash, get_hash(self.script))

        with mock.patch('substrapp.utils.requests.get') as mget:
            mget.return_value = HttpResponse()
            mget.return_value.status_code = status.HTTP_400_BAD_REQUEST
            with self.assertRaises(Exception):
                get_computed_hash('localhost')

    def test_get_remote_file(self):
        content = str(self.script.read())
        remote_file = {'storageAddress': 'localhost',
                       'hash': compute_hash(content)}

        with mock.patch('substrapp.utils.get_computed_hash') as mget_computed_hash:
            pkhash = compute_hash(content)
            mget_computed_hash.return_value = content, pkhash

            content_remote, pkhash_remote = get_remote_file(remote_file)
            self.assertEqual(pkhash_remote, get_hash(self.script))
            self.assertEqual(content_remote, content)

        with mock.patch('substrapp.utils.get_computed_hash') as mget_computed_hash:
            content = content + ' FAIL'
            pkhash = compute_hash(content)
            mget_computed_hash.return_value = content, pkhash

            with self.assertRaises(Exception):
                get_remote_file(remote_file)  # contents (by pkhash) are different

    def test_Ressource_Manager(self):

        self.assertTrue(isinstance(self.ResourcesManager.memory_limit_mb(), int))

        cpu_set, gpu_set = self.ResourcesManager.get_cpu_gpu_sets()
        self.assertIn(cpu_set, self.ResourcesManager._ResourcesManager__cpu_sets)

        if gpu_set is not None:
            self.assertIn(gpu_set, self.ResourcesManager._ResourcesManager__gpu_sets)

    def test_monitoring_task(self):

        monitoring = ExceptionThread(target=monitoring_task, args=(FakeClient(), {'name': 'job'}))
        monitoring.start()
        time.sleep(0.1)
        monitoring.join()

        self.assertNotEqual(monitoring._stats['memory']['max'], 0)
        self.assertNotEqual(monitoring._stats['cpu']['max'], 0)
        self.assertNotEqual(monitoring._stats['netio']['rx'], 0)

    def test_put_algo_tar(self):
        algo_content = self.algo.read()
        subtuple_key = get_hash(self.algo)

        subtuple = {'key': subtuple_key,
                    'algo': 'testalgo'}

        with mock.patch('substrapp.tasks.get_hash') as mget_hash:
            mget_hash.return_value = subtuple_key
            put_algo(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/'), algo_content)

        def tree_printer(root):
            for root, dirs, files in os.walk(root):
                for d in dirs:
                    print(os.path.join(root, d))
                for f in files:
                    print(os.path.join(root, f))

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

        with mock.patch('substrapp.tasks.get_hash') as mget_hash:
            with open(zippath, 'rb') as content:
                mget_hash.return_value = get_hash(zippath)
                put_algo(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/'), content.read())

        self.assertTrue(os.path.exists(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}/{filename}')))

    def test_put_metric(self):

        filepath = os.path.join(self.subtuple_path, self.script_filename)
        with open(filepath, 'w') as f:
            f.write(self.script.read())
        self.assertTrue(os.path.exists(filepath))

        metrics_directory = os.path.join(self.subtuple_path, 'metrics/')
        create_directory(metrics_directory)

        put_metric(self.subtuple_path, FakeObjective(filepath))
        self.assertTrue(os.path.exists(os.path.join(metrics_directory, 'metrics.py')))

    def test_put_opener(self):

        filepath = os.path.join(self.subtuple_path, self.script_filename)
        with open(filepath, 'w') as f:
            f.write(self.script.read())
        self.assertTrue(os.path.exists(filepath))

        opener_directory = os.path.join(self.subtuple_path, 'opener')
        create_directory(opener_directory)

        with mock.patch('substrapp.models.DataManager.objects.get') as mget:
            mget.return_value = FakeDataManager(filepath)

            # test fail
            with self.assertRaises(Exception):
                put_opener({'dataset': {'openerHash': 'HASH'}}, self.subtuple_path)

            # test work
            put_opener({'dataset': {'openerHash': get_hash(filepath)}}, self.subtuple_path)

        self.assertTrue(os.path.exists(os.path.join(opener_directory, 'opener.py')))

    def test_put_data_sample_zip(self):

        data_sample = DataSample(pkhash='foo', path=self.data_sample)
        data_sample.save()

        subtuple = {
            'key': 'bar',
            'dataset': {'keys': [data_sample.pk]}
        }

        with mock.patch('substrapp.models.DataSample.objects.get') as mget:
            mget.return_value = data_sample

            subtuple_direcory = build_subtuple_folders(subtuple)

            put_data_sample(subtuple, subtuple_direcory)

            # check folder has been correctly renamed with pk of directory containing uncompressed data sample
            self.assertFalse(
                os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', 'foo')))
            dir_pkhash = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'
            self.assertTrue(
                os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', dir_pkhash)))

            # check subtuple folder has been created and sym links exists
            self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk)))
            self.assertTrue(os.path.islink(os.path.join(MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk)))
            self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk, 'LABEL_0024900.csv')))
            self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk, 'IMG_0024900.jpg')))

    def test_put_data_tar(self):

        data_sample = DataSample(pkhash='foo', path=self.data_sample_tar)
        data_sample.save()

        subtuple = {
            'key': 'bar',
            'dataset': {'keys': [data_sample.pk]}
        }

        with mock.patch('substrapp.models.DataSample.objects.get') as mget:
            mget.return_value = data_sample

            subtuple_direcory = build_subtuple_folders(subtuple)

            put_data_sample(subtuple, subtuple_direcory)

            # check folder has been correctly renamed with pk of directory containing uncompressed data_sample
            self.assertFalse(os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', 'foo')))
            dir_pkhash = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'
            self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'datasamples', dir_pkhash)))

            # check subtuple folder has been created and sym links exists
            self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk)))
            self.assertTrue(os.path.islink(os.path.join(MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk)))
            self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk, 'LABEL_0024900.csv')))
            self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'subtuple/bar/data', data_sample.pk, 'IMG_0024900.jpg')))

    def test_put_model(self):

        model_content = self.model.read().encode()

        traintupleKey = compute_hash(model_content)
        model_hash = compute_hash(model_content, traintupleKey)
        model_type = 'model'
        subtuple = {'key': model_hash, model_type: {'hash': model_hash, 'traintupleKey': traintupleKey}}

        model_directory = os.path.join(self.subtuple_path, 'model')
        create_directory(model_directory)
        put_model(subtuple, self.subtuple_path, model_content)

        model_path = os.path.join(model_directory, traintupleKey)
        self.assertTrue(os.path.exists(model_path))

        os.rename(model_path, model_path + '-local')
        with mock.patch('substrapp.models.Model.objects.get') as mget:
            mget.return_value = FakeModel(model_path + '-local')
            put_model(subtuple, self.subtuple_path, model_content)
            self.assertTrue(os.path.exists(model_path))

        with mock.patch('substrapp.models.Model.objects.get') as mget:
            mget.return_value = FakeModel(model_path)
            with self.assertRaises(Exception):
                put_model({'model': {'hash': 'fail-hash'}}, self.subtuple_path, model_content)

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
        subtuple = {model_type: [{'hash': model_hash, 'traintupleKey': traintupleKey},
                                 {'hash': model_hash2, 'traintupleKey': traintupleKey2}]}

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

    def test_get_model(self):
        model_content = self.model.read().encode()
        traintupleKey = compute_hash(model_content)
        model_hash = compute_hash(model_content, traintupleKey)
        model_type = 'model'
        subtuple = {model_type: {'hash': model_hash, 'traintupleKey': traintupleKey}}

        with mock.patch('substrapp.tasks.get_remote_file') as mget_remote_file:
            mget_remote_file.return_value = model_content, model_hash
            model_content, model_hash = get_model(subtuple)

        self.assertIsNotNone(model_content)
        self.assertIsNotNone(model_hash)

    def test_get_models(self):
        model_content = self.model.read().encode()
        models_content = [model_content, model_content + b', -2.0']

        traintupleKey = compute_hash(models_content[0])
        model_hash = compute_hash(models_content[0], traintupleKey)

        traintupleKey2 = compute_hash(models_content[1])
        model_hash2 = compute_hash(models_content[1], traintupleKey2)

        models_hash = [model_hash, model_hash2]
        model_type = 'inModels'
        subtuple = {model_type: [{'hash': model_hash, 'traintupleKey': traintupleKey},
                                 {'hash': model_hash2, 'traintupleKey': traintupleKey2}]}

        with mock.patch('substrapp.tasks.get_remote_file') as mget_remote_file:
            mget_remote_file.side_effect = [[models_content[0], models_hash[0]],
                                            [models_content[1], models_hash[1]]]
            models_content_res, models_hash_res = get_models(subtuple)

        self.assertEqual(models_content_res, models_content)
        self.assertIsNotNone(models_hash_res, models_hash)

    def test_get_algo(self):
        algo_content = self.algo.read()
        algo_hash = get_hash(self.algo)

        with mock.patch('substrapp.tasks.get_remote_file') as mget_remote_file:
            mget_remote_file.return_value = algo_content, algo_hash
            self.assertEqual((algo_content, algo_hash), get_algo({'algo': ''}))

    def test_get_objective(self):
        metrics_content = self.script.read()
        objective_hash = get_hash(self.script)

        with mock.patch('substrapp.models.Objective.objects.get') as mget, \
                mock.patch('substrapp.tasks.get_remote_file') as mget_remote_file, \
                mock.patch('substrapp.models.Objective.objects.update_or_create') as mupdate_or_create:

                mget.return_value = FakeObjective()
                mget_remote_file.return_value = metrics_content, objective_hash
                mupdate_or_create.return_value = FakeObjective(), True

                objective = get_objective({'objective': {'hash': objective_hash,
                                           'metrics': ''}})
                self.assertTrue(isinstance(objective, FakeObjective))

    def test_compute_docker(self):
        cpu_set, gpu_set = None, None
        client = docker.from_env()

        dockerfile_path = os.path.join(self.subtuple_path, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write('FROM library/hello-world')

        result = compute_docker(client, self.ResourcesManager,
                                self.subtuple_path, 'test_compute_docker',
                                'test_compute_docker_name', None, None)

        self.assertIsNone(cpu_set)
        self.assertIsNone(gpu_set)

        self.assertIn('CPU', result)
        self.assertIn('GPU', result)
        self.assertIn('Mem', result)
        self.assertIn('GPU Mem', result)

    def test_build_subtuple_folders(self):
        with mock.patch('substrapp.tasks.getattr') as getattr:
            getattr.return_value = self.subtuple_path

            subtuple_key = 'test1234'
            subtuple = {'key': subtuple_key}
            subtuple_directory = build_subtuple_folders(subtuple)

            self.assertTrue(os.path.exists(subtuple_directory))
            self.assertEqual(os.path.join(self.subtuple_path, f'subtuple/{subtuple["key"]}'), subtuple_directory)

            for root, dirs, files in os.walk(subtuple_directory):
                nb_subfolders = len(dirs)

            self.assertTrue(5, nb_subfolders)

    def test_prepareTasks(self):

        class FakeSettings(object):
            def __init__(self):
                self.LEDGER = {'signcert': 'signcert',
                               'org': 'owkin',
                               'peer': 'peer'}

                self.MEDIA_ROOT = MEDIA_ROOT

        subtuple = [{'key': 'subtuple_test'}]

        with mock.patch('substrapp.tasks.settings') as msettings, \
                mock.patch('substrapp.tasks.get_hash') as mget_hash, \
                mock.patch('substrapp.tasks.queryLedger') as mqueryLedger, \
                mock.patch('substrapp.tasks.get_objective') as mget_objective, \
                mock.patch('substrapp.tasks.get_algo') as mget_algo, \
                mock.patch('substrapp.tasks.get_model') as mget_model, \
                mock.patch('substrapp.tasks.build_subtuple_folders') as mbuild_subtuple_folders, \
                mock.patch('substrapp.tasks.put_opener') as mput_opener, \
                mock.patch('substrapp.tasks.put_data_sample') as mput_data_sample, \
                mock.patch('substrapp.tasks.put_metric') as mput_metric, \
                mock.patch('substrapp.tasks.put_algo') as mput_algo, \
                mock.patch('substrapp.tasks.put_model') as mput_model:

                msettings.return_value = FakeSettings()
                mget_hash.return_value = 'owkinhash'
                mqueryLedger.return_value = subtuple, 200
                mget_objective.return_value = 'objective'
                mget_algo.return_value = 'algo', 'algo_hash'
                mget_model.return_value = 'model', 'model_hash'
                mbuild_subtuple_folders.return_value = MEDIA_ROOT
                mput_opener.return_value = 'opener'
                mput_data_sample.return_value = 'data'
                mput_metric.return_value = 'metric'
                mput_algo.return_value = 'algo'
                mput_model.return_value = 'model'

                with mock.patch('substrapp.tasks.queryLedger') as mqueryLedger:
                    mqueryLedger.return_value = 'data', 404
                    prepareTask('traintuple', 'inModels')

                with mock.patch('substrapp.tasks.invokeLedger') as minvokeLedger, \
                        mock.patch('substrapp.tasks.computeTask.apply_async') as mapply_async:
                        minvokeLedger.return_value = 'data', 201
                        mapply_async.return_value = 'doTask'
                        prepareTask('traintuple', 'inModels')

    def test_doTask(self):

        class FakeSettings(object):
            def __init__(self):
                self.LEDGER = {'signcert': 'signcert',
                               'org': 'owkin',
                               'peer': 'peer'}

                self.MEDIA_ROOT = MEDIA_ROOT

        subtuple_key = 'test_owkin'
        subtuple = {'key': subtuple_key, 'inModels': None}
        subtuple_directory = build_subtuple_folders(subtuple)

        with mock.patch('substrapp.tasks.settings') as msettings, \
                mock.patch('substrapp.tasks.getattr') as mgetattr, \
                mock.patch('substrapp.tasks.invokeLedger') as minvokeLedger:
            msettings.return_value = FakeSettings()
            mgetattr.return_value = self.subtuple_path
            minvokeLedger.return_value = 'data', 200

            for name in ['opener', 'metrics']:
                with open(os.path.join(subtuple_directory, f'{name}/{name}.py'), 'w') as f:
                    f.write('Hello World')

            perf = 0.3141592
            with open(os.path.join(subtuple_directory, 'pred/perf.json'), 'w') as f:
                f.write(f'{{"all": {perf}}}')

            with open(os.path.join(subtuple_directory, 'model/model'), 'w') as f:
                f.write("MODEL")

            with mock.patch('substrapp.tasks.compute_docker') as mcompute_docker:
                mcompute_docker.return_value = 'DONE'
                doTask(subtuple, 'traintuple')

    def test_computeTask(self):

        class FakeSettings(object):
            def __init__(self):
                self.LEDGER = {'signcert': 'signcert',
                               'org': 'owkin',
                               'peer': 'peer'}

                self.MEDIA_ROOT = MEDIA_ROOT

        subtuple_key = 'test_owkin'
        subtuple = {'key': subtuple_key, 'inModels': None}
        subtuple_directory = build_subtuple_folders(subtuple)

        with mock.patch('substrapp.tasks.settings') as msettings, \
                mock.patch('substrapp.tasks.getattr') as mgetattr, \
                mock.patch('substrapp.tasks.invokeLedger') as minvokeLedger:
            msettings.return_value = FakeSettings()
            mgetattr.return_value = self.subtuple_path
            minvokeLedger.return_value = 'data', 200

            for name in ['opener', 'metrics']:
                with open(os.path.join(subtuple_directory, f'{name}/{name}.py'), 'w') as f:
                    f.write('Hello World')

            perf = 0.3141592
            with open(os.path.join(subtuple_directory, 'pred/perf.json'), 'w') as f:
                f.write(f'{{"all": {perf}}}')

            with open(os.path.join(subtuple_directory, 'model/model'), 'w') as f:
                f.write("MODEL")

            with mock.patch('substrapp.tasks.compute_docker') as mcompute_docker, \
                    mock.patch('substrapp.tasks.prepareMaterials') as mprepareMaterials, \
                    mock.patch('substrapp.tasks.invokeLedger') as minvokeLedger:

                mcompute_docker.return_value = 'DONE'
                mprepareMaterials.return_value = 'DONE'
                minvokeLedger.return_value = 'data', 201

                computeTask('traintuple', subtuple, 'inModels', None)

import os
import shutil
import tempfile

import mock
import time

from django.test import override_settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.utils import compute_hash, get_computed_hash, get_remote_file, get_hash, create_directory
from substrapp.job_utils import RessourceManager, monitoring_job, compute_docker
from substrapp.tasks import build_traintuple_folders, get_algo, get_model, get_challenge, put_opener, put_model, put_algo, put_metric, put_data, prepareTask, doTask

from .common import get_sample_challenge, get_sample_dataset, get_sample_data, get_sample_script

import tarfile
import zipfile
from threading import Thread
from .tests_misc import Stats
import docker
MEDIA_ROOT = "/tmp/unittests_tasks/"
# MEDIA_ROOT = tempfile.mkdtemp()


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TasksTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.traintuple_path = MEDIA_ROOT

        self.challenge_description, self.challenge_description_filename, \
            self.challenge_metrics, self.challenge_metrics_filename = get_sample_challenge()

        self.script, self.script_filename = get_sample_script()
        self.data_file, self.data_file_filename = get_sample_data()

        self.data_description, self.data_description_filename, self.data_data_opener, \
            self.data_opener_filename = get_sample_dataset()

        self.RessourceManager = RessourceManager()

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
            _, pkhash = get_computed_hash('test')
            self.assertEqual(pkhash, 'da920c804c4724f1ce7bd0484edcf4aafa209d5bd54e2e89972c087a487cbe02')

        with mock.patch('substrapp.utils.requests.get') as mget:
            mget.return_value = HttpResponse()
            mget.return_value.status_code = status.HTTP_400_BAD_REQUEST
            with self.assertRaises(Exception):
                get_computed_hash('test')

    def test_get_remote_file(self):
        remote_file = {'storageAddress': 'test',
                       'hash': 'da920c804c4724f1ce7bd0484edcf4aafa209d5bd54e2e89972c087a487cbe02'}

        with mock.patch('substrapp.utils.get_computed_hash') as mget_computed_hash:
            content = str(self.script.read())
            pkhash = compute_hash(content)
            mget_computed_hash.return_value = content, pkhash

            content_remote, pkhash_remote = get_remote_file(remote_file)
            self.assertEqual(pkhash_remote, 'da920c804c4724f1ce7bd0484edcf4aafa209d5bd54e2e89972c087a487cbe02')
            self.assertEqual(content_remote, content)

        with mock.patch('substrapp.utils.get_computed_hash') as mget_computed_hash:
            content = str(self.script.read()) + ' FAIL'
            pkhash = compute_hash(content)
            mget_computed_hash.return_value = content, pkhash

            with self.assertRaises(Exception):
                get_remote_file(remote_file)

    def test_Ressource_Manager(self):

        self.assertIn('M', self.RessourceManager.memory_limit_mb())

        cpu_set = self.RessourceManager.acquire_cpu_set()
        self.assertIn(cpu_set, self.RessourceManager._RessourceManager__used_cpu_sets)
        self.RessourceManager.return_cpu_set(cpu_set)
        self.assertNotIn(cpu_set, self.RessourceManager._RessourceManager__used_cpu_sets)

        gpu_set = self.RessourceManager.acquire_gpu_set()
        if gpu_set != 'no_gpu':
            self.assertIn(gpu_set, self.RessourceManager._RessourceManager__used_gpu_sets)
        self.RessourceManager.return_gpu_set(gpu_set)
        self.assertNotIn(gpu_set, self.RessourceManager._RessourceManager__used_gpu_sets)

    def test_monitoring_job(self):

        class FakeContainer(object):
            def __init__(self):
                self.c_stats = Stats.get_stats()

            def stats(self, decode, stream):
                return self.c_stats

        class FakeClient(object):
            def __init__(self):
                self.containers = {'job': FakeContainer()}

        monitoring = Thread(target=monitoring_job, args=(FakeClient(), {'name': 'job'}))
        monitoring.start()
        time.sleep(0.1)
        monitoring.do_run = False
        monitoring.join()

        self.assertNotEqual(monitoring._stats['memory']['max'], 0)
        self.assertNotEqual(monitoring._stats['cpu']['max'], 0)
        self.assertNotEqual(monitoring._stats['netio']['rx'], 0)

    def test_put_algo(self):

        filename = 'algo.py'
        filepath = os.path.join(self.traintuple_path, filename)
        with open(filepath, 'w') as f:
            f.write('Hello World')
        self.assertTrue(os.path.exists(filepath))

        tarname = 'sample.tar.gz'
        tarpath = os.path.join(self.traintuple_path, tarname)
        with tarfile.open(tarpath, mode='w:gz') as tf:
            tf.add(filepath, arcname=filename)
        self.assertTrue(os.path.exists(tarpath))

        traintuple_key = 'testkey'
        traintuple = {'key': traintuple_key, 'algo': 'testalgo'}

        with mock.patch('substrapp.tasks.get_hash') as mget_hash:
            with open(tarpath, 'rb') as content:
                mget_hash.return_value = get_hash(tarpath)
                put_algo(traintuple, os.path.join(self.traintuple_path, 'traintuple/%s/' % traintuple['key']), content.read())

        self.assertTrue(os.path.exists(os.path.join(self.traintuple_path, 'traintuple/%s/%s' % (traintuple['key'], filename))))

    def test_put_metric(self):

        class FakeMetrics(object):
            def __init__(self, filepath):
                self.path = filepath

        class FakeChallenge(object):
            def __init__(self, filepath):
                self.metrics = FakeMetrics(filepath)

        filename = 'sample_metrics.py'
        filepath = os.path.join(self.traintuple_path, filename)
        with open(filepath, 'w') as f:
            f.write('Hello World')
        self.assertTrue(os.path.exists(filepath))

        metrics_directory = os.path.join(self.traintuple_path, 'metrics/')
        create_directory(metrics_directory)

        put_metric(self.traintuple_path, FakeChallenge(filepath))
        self.assertTrue(os.path.exists(os.path.join(metrics_directory, 'metrics.py')))

    def test_put_opener(self):

        class FakeOpener(object):
            def __init__(self, filepath):
                self.path = filepath

        class FakeDataset(object):
            def __init__(self, filepath):
                self.data_opener = FakeOpener(filepath)

        filename = 'opener.py'
        filepath = os.path.join(self.traintuple_path, filename)
        with open(filepath, 'w') as f:
            f.write('Hello World')
        self.assertTrue(os.path.exists(filepath))

        data_type = 'trainData'
        traintuple = {data_type: {'openerHash': get_hash(filepath)}}

        opener_directory = os.path.join(self.traintuple_path, 'opener')
        create_directory(opener_directory)

        with mock.patch('substrapp.models.Dataset.objects.get') as mget:
            mget.return_value = FakeDataset(filepath)

            # test fail
            with self.assertRaises(Exception):
                put_opener({data_type: {'openerHash': 'HASH'}}, self.traintuple_path, data_type)

            # test work
            put_opener(traintuple, self.traintuple_path, data_type)

        self.assertTrue(os.path.exists(os.path.join(opener_directory, 'opener.py')))

    def test_put_data(self):

        data_directory = os.path.join(self.traintuple_path, 'data/')
        create_directory(data_directory)

        filename = 'data.csv'
        filepath = os.path.join(self.traintuple_path, filename)
        with open(filepath, 'w') as f:
            f.write('Hello World')
        self.assertTrue(os.path.exists(filepath))

        zippath = os.path.join(self.traintuple_path, 'sample.zip')
        with zipfile.ZipFile(zippath, 'w') as myzip:
            myzip.write(filepath)
        self.assertTrue(os.path.exists(zippath))

        data_type = 'trainData'
        data_hash = get_hash(zippath)
        traintuple = {data_type: {'keys': [data_hash]}}

        class FakeFile(object):
            def __init__(self, filepath):
                self.path = filepath
                self.name = self.path

        class FakeData(object):
            def __init__(self, filepath):
                self.file = FakeFile(filepath)

        with mock.patch('substrapp.models.Data.objects.get') as mget:
            mget.return_value = FakeData(zippath)
            put_data(traintuple, MEDIA_ROOT, data_type)

    def test_put_model(self):

        class FakePath(object):
            def __init__(self, filepath):
                self.path = filepath

        class FakeModel(object):
            def __init__(self, filepath):
                self.file = FakePath(filepath)

        modelpath = os.path.join(self.traintuple_path, 'model/model')
        model_content = b'MODEL 1 2 3'
        model_hash = compute_hash(model_content)
        model_type = 'startModel'
        traintuple = {model_type: {'hash': model_hash}}

        model_directory = os.path.join(self.traintuple_path, 'model/')
        create_directory(model_directory)

        put_model(traintuple, self.traintuple_path, model_content, model_type)
        self.assertTrue(os.path.exists(modelpath))

        os.rename(modelpath, modelpath + '-tmp')
        with mock.patch('substrapp.models.Model.objects.get') as mget:
            mget.return_value = FakeModel(modelpath + '-tmp')
            put_model(traintuple, self.traintuple_path, model_content, model_type)
            self.assertTrue(os.path.exists(modelpath))

        with mock.patch('substrapp.models.Model.objects.get') as mget:
            mget.return_value = FakeModel(modelpath)
            with self.assertRaises(Exception):
                put_model({'startModel': {'hash': 'hash'}}, self.traintuple_path, model_content, model_type)

    def test_get_model(self):
        model_content = b'MODEL 1 2 3'
        model_hash = compute_hash(model_content)
        model_type = 'startModel'
        traintuple = {model_type: {'hash': model_hash}}

        with mock.patch('substrapp.tasks.get_remote_file') as mget_remote_file:
            mget_remote_file.return_value = model_content, model_hash
            model_content, model_hash = get_model(traintuple, model_type)

        self.assertIsNotNone(model_content)
        self.assertIsNotNone(model_hash)

    def test_get_algo(self):
        algo_content, algo_hash = 'content', 'hash'
        traintuple = {'algo': 'myalgo'}

        with mock.patch('substrapp.tasks.get_remote_file') as mget_remote_file:
            mget_remote_file.return_value = algo_content, algo_hash
            self.assertEqual((algo_content, algo_hash), get_algo(traintuple))

    def test_get_challenge(self):
        metrics_content = b'Metric 1 2 3'
        challenge_hash = compute_hash(metrics_content)
        traintuple = {'challenge': {'hash': challenge_hash,
                                    'metrics': 'metrics.py'}}

        class FakeMetrics(object):
            def __init__(self):
                self.path = 'path'

            def save(self, p, f):
                return

        class FakeChallenge(object):
            def __init__(self, metrics=FakeMetrics()):
                self.metrics = metrics

        with mock.patch('substrapp.models.Challenge.objects.get') as mget:
            mget.return_value = FakeChallenge()

        with mock.patch('substrapp.models.Challenge.objects.get') as mget, \
                mock.patch('substrapp.tasks.get_remote_file') as mget_remote_file, \
                mock.patch('substrapp.models.Challenge.objects.update_or_create') as mupdate_or_create:

                mget.return_value = FakeChallenge(False)
                mget_remote_file.return_value = metrics_content, challenge_hash
                mupdate_or_create.return_value = FakeChallenge(), True

                challenge = get_challenge(traintuple)
                self.assertTrue(isinstance(challenge, FakeChallenge))

    def test_compute_docker(self):
        cpu_set, gpu_set = None, None
        client = docker.from_env()

        dockerfile_path = os.path.join(self.traintuple_path, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write('FROM library/hello-world')

        result = compute_docker(client, self.RessourceManager,
                                self.traintuple_path, 'test_compute_docker',
                                'test_compute_docker_name', None, None, cpu_set, gpu_set)

        self.assertIsNone(cpu_set)
        self.assertIsNone(gpu_set)

        self.assertIn('CPU', result)
        self.assertIn('GPU', result)
        self.assertIn('Mem', result)
        self.assertIn('GPU Mem', result)

    def test_build_traintuple_folders(self):
        with mock.patch('substrapp.tasks.getattr') as getattr:
            getattr.return_value = self.traintuple_path

            traintuple_key = 'test1234'
            traintuple = {'key': traintuple_key}
            traintuple_directory = build_traintuple_folders(traintuple)

            self.assertTrue(os.path.exists(traintuple_directory))
            self.assertEqual(os.path.join(self.traintuple_path, 'traintuple/%s' % traintuple['key']), traintuple_directory)

            for root, dirs, files in os.walk(traintuple_directory):
                nb_subfolders = len(dirs)

            self.assertTrue(5, nb_subfolders)

    def test_prepareTasks(self):

        class FakeSettings(object):
            def __init__(self):
                self.LEDGER = {'signcert': 'signcert',
                               'org': 'owkin',
                               'peer': 'peer'}

                self.MEDIA_ROOT = MEDIA_ROOT

        traintuple = [{'key': 'traintuple_test'
                       }]

        with mock.patch('substrapp.tasks.settings') as msettings, \
                mock.patch('substrapp.tasks.get_hash') as mget_hash, \
                mock.patch('substrapp.tasks.queryLedger') as mqueryLedger, \
                mock.patch('substrapp.tasks.get_challenge') as mget_challenge, \
                mock.patch('substrapp.tasks.get_algo') as mget_algo, \
                mock.patch('substrapp.tasks.get_model') as mget_model, \
                mock.patch('substrapp.tasks.build_traintuple_folders') as mbuild_traintuple_folders, \
                mock.patch('substrapp.tasks.put_opener') as mput_opener, \
                mock.patch('substrapp.tasks.put_data') as mput_data, \
                mock.patch('substrapp.tasks.put_metric') as mput_metric, \
                mock.patch('substrapp.tasks.put_algo') as mput_algo, \
                mock.patch('substrapp.tasks.put_model') as mput_model:

                msettings.return_value = FakeSettings()
                mget_hash.return_value = 'owkinhash'
                mqueryLedger.return_value = traintuple, 200
                mget_challenge.return_value = 'challenge'
                mget_algo.return_value = 'algo', 'algo_hash'
                mget_model.return_value = 'model', 'model_hash'
                mbuild_traintuple_folders.return_value = MEDIA_ROOT
                mput_opener.return_value = 'opener'
                mput_data.return_value = 'data'
                mput_metric.return_value = 'metric'
                mput_algo.return_value = 'algo'
                mput_model.return_value = 'model'

                with mock.patch('substrapp.tasks.invokeLedger') as minvokeLedger:
                    minvokeLedger.return_value = 'data', 404
                    with self.assertLogs(level='ERROR') as cm:
                        prepareTask('trainData', 'trainWorker', 'todo', 'startModel', 'training')
                        self.assertEqual(cm.output, ['ERROR:root:Failed to invoke ledger on prepareTask trainData'])

                with mock.patch('substrapp.tasks.invokeLedger') as minvokeLedger, \
                        mock.patch('substrapp.tasks.doTask.apply_async') as mapply_async:
                        minvokeLedger.return_value = 'data', 201
                        mapply_async.return_value = 'doTask'

                        with self.assertLogs(level='INFO') as cm:
                            prepareTask('trainData', 'trainWorker', 'todo', 'startModel', 'training')
                            self.assertEqual(cm.output, ['INFO:root:Prepare Task success trainData'])

    def test_doTask(self):

        class FakeSettings(object):
            def __init__(self):
                self.LEDGER = {'signcert': 'signcert',
                               'org': 'owkin',
                               'peer': 'peer'}

                self.MEDIA_ROOT = MEDIA_ROOT

        traintuple_key = 'test_owkin'
        traintuple = {'key': traintuple_key}
        traintuple_directory = build_traintuple_folders(traintuple)

        with mock.patch('substrapp.tasks.settings') as msettings, \
                mock.patch('substrapp.tasks.getattr') as mgetattr, \
                mock.patch('substrapp.tasks.invokeLedger') as minvokeLedger:
            msettings.return_value = FakeSettings()
            mgetattr.return_value = self.traintuple_path
            minvokeLedger.return_value = 'data', 200

            for name in ['opener', 'metrics']:
                with open(os.path.join(traintuple_directory, '%s/%s.py' % (name, name)), 'w') as f:
                    f.write('Hello World')

            perf = 0.3141592
            with open(os.path.join(traintuple_directory, 'pred/perf.json'), 'w') as f:
                f.write('{"all": %s}' % perf)

            with open(os.path.join(traintuple_directory, 'model/model'), 'w') as f:
                f.write("MODEL")

            with mock.patch('substrapp.tasks.compute_docker') as mcompute_docker:
                mcompute_docker.return_value = 'TRAINED'
                doTask(traintuple, 'trainData')

                name, args, kwargs = minvokeLedger.mock_calls[0]
                ARGS_INVOKE = args[0]['args']
                self.assertIn(f'{perf}', ARGS_INVOKE)
                self.assertIn('logSuccessTrain', ARGS_INVOKE)
                self.assertIn('TRAINED', ARGS_INVOKE)
                self.assertIn(traintuple_key, ARGS_INVOKE)

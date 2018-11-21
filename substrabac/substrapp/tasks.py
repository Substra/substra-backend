from __future__ import absolute_import, unicode_literals

import os
import io
import tarfile
import tempfile
from os import path

import requests
from django.conf import settings
from rest_framework.reverse import reverse

from substrabac.celery import app
from substrapp.utils import queryLedger, invokeLedger
from .utils import compute_hash, update_statistics, get_cpu_sets, get_gpu_sets, ExceptionThread
from .exception_handler import compute_error_code

import docker
import json
import time
import threading
from multiprocessing.managers import BaseManager

import logging

import GPUtil as gputil


def create_directory(directory):
    if not path.exists(directory):
        os.makedirs(directory)


def get_hash(file):
    with open(file, 'rb') as f:
        data = f.read()
        return compute_hash(data)


def get_computed_hash(url):
    kwargs = {}
    username = getattr(settings, 'BASICAUTH_USERNAME', None)
    password = getattr(settings, 'BASICAUTH_PASSWORD', None)

    if username is not None and password is not None:
        kwargs = {
            'auth': (username, password),
            'verify': False
        }

    try:
        r = requests.get(url, headers={'Accept': 'application/json;version=0.0'}, **kwargs)
    except:
        raise Exception('Failed to check hash due to failed file fetching %s' % url)
    else:
        if r.status_code != 200:
            raise Exception(
                'Url: %(url)s to fetch file returned status code: %(st)s' % {'url': url, 'st': r.status_code})

        computedHash = compute_hash(r.content)

        return r.content, computedHash


def get_remote_file(object):
    content, computed_hash = get_computed_hash(object['storageAddress'])  # TODO pass cert

    if computed_hash != object['hash']:
        msg = 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'
        raise Exception(msg)

    return content, computed_hash


def fail(key, err_msg):
    # Log Fail TrainTest
    data, st = invokeLedger({
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["logFailTrainTest","%(key)s","%(err_msg)s"]}' % {'key': key,
                                                                           'err_msg': str(err_msg).replace('"',
                                                                                                           "'").replace(
                                                                               '\\', "").replace('\\n', "")[:200]}
    })

    if st != 201:
        logging.error(data, exc_info=True)

    logging.info('Successfully passed the traintuple to failed')
    return data


def untar_algo(content, directory, traintuple):
    try:
        tar = tarfile.open(fileobj=io.BytesIO(content))
        tar.extractall(directory)
        tar.close()
    except:
        return fail(traintuple['key'], 'Fail to untar algo file')


def monitoring_job(client, job_args):
    """thread worker function"""

    job_name = job_args['name']

    gpu_set = None
    if 'environment' in job_args:
        gpu_set = job_args['environment']['NVIDIA_VISIBLE_DEVICES']

    start = time.time()
    t = threading.currentThread()

    # Statistics
    job_statistics = {'memory': {'max': 0,
                                 'current': [0]},
                      'gpu_memory': {'max': 0,
                                     'current': [0]},
                      'cpu': {'max': 0,
                              'current': [0]},
                      'gpu': {'max': 0,
                              'current': []},
                      'io': {'max': 0,
                             'current': []},
                      'netio': {'rx': 0,
                                'tx': 0},
                      'time': 0}

    while getattr(t, "do_run", True):
        stats = None
        try:
            container = client.containers.get(job_name)
            stats = container.stats(decode=True, stream=False)
        except:
            pass

        gpu_stats = None
        if gpu_set is not None:
            gpu_stats = [gpu for gpu in gputil.getGPUs() if str(gpu.id) in gpu_set]

        update_statistics(job_statistics, stats, gpu_stats)

    job_statistics['time'] = time.time() - start

    t._result = 'CPU:%.2f %% - Mem:%.2f GB - GPU:%.2f %% - GPU Mem:%.2f GB' % (job_statistics['cpu']['max'],
                                                                               job_statistics['memory']['max'],
                                                                               job_statistics['gpu']['max'],
                                                                               job_statistics['gpu_memory']['max'])

    t._stats = job_statistics


class RessourceManager():
    __concurrency = int(os.environ.get('CELERYD_CONCURRENCY', 1))
    __memory_gb = int(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024. ** 2))

    __cpu_count = os.cpu_count()
    __cpu_sets = get_cpu_sets(__cpu_count, __concurrency)

    # Set CUDA_DEVICE_ORDER so the IDs assigned by CUDA match those from nvidia-smi
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    __gpu_list = [str(gpu.id) for gpu in gputil.getGPUs()]

    __gpu_sets = 'no_gpu'
    if __gpu_list:
        __gpu_sets = get_gpu_sets(__gpu_list, __concurrency)

    __used_cpu_sets = []
    __used_gpu_sets = []
    __lock = threading.Lock()

    @classmethod
    def memory_limit_mb(cls):
        return '%sM' % (cls.__memory_gb // cls.__concurrency)

    @classmethod
    def acquire_cpu_set(cls):
        cpu_set = None
        cls.__lock.acquire()

        try:
            cpu_set_available = set(cls.__cpu_sets).difference(set(cls.__used_cpu_sets))
            if len(cpu_set_available) > 0:
                cpu_set = cpu_set_available.pop()
                cls.__used_cpu_sets.append(cpu_set)
        except:
            pass

        cls.__lock.release()
        return cpu_set

    @classmethod
    def return_cpu_set(cls, cpu_set):
        cls.__lock.acquire()

        try:
            cls.__used_cpu_sets.remove(cpu_set)
        except:
            pass

        cls.__lock.release()

    @classmethod
    def acquire_gpu_set(cls):
        gpu_set = 'no_gpu'
        cls.__lock.acquire()

        if cls.__gpu_sets != 'no_gpu':
            gpu_set = None
            try:
                gpu_set_available = set(cls.__gpu_sets).difference(set(cls.__used_gpu_sets))
                if len(gpu_set_available) > 0:
                    gpu_set = gpu_set_available.pop()
                    cls.__used_gpu_sets.append(gpu_set)
            except:
                pass

        cls.__lock.release()
        return gpu_set

    @classmethod
    def return_gpu_set(cls, gpu_set):
        cls.__lock.acquire()

        if gpu_set != 'no_gpu':
            try:
                cls.__used_gpu_sets.remove(gpu_set)
            except:
                pass

        cls.__lock.release()


# Instatiate Ressource Manager
BaseManager.register('RessourceManager', RessourceManager)
manager = BaseManager()
manager.start()
ressource_manager = manager.RessourceManager()


def prepareTask(data_type, worker_to_filter, status_to_filter, model_type, status_to_set):
    from shutil import copy
    import zipfile
    from substrapp.models import Challenge, Dataset, Data, Model, Algo

    try:
        data_owner = get_hash(settings.LEDGER['signcert'])
    except Exception as e:
        logging.error(e, exc_info=True)
    else:
        traintuples, st = queryLedger({
            'org': settings.LEDGER['org'],
            'peer': settings.LEDGER['peer'],
            'args': '{"Args":["queryFilter","traintuple~%s~status","%s,%s"]}' % (
                worker_to_filter, data_owner, status_to_filter)
        })

        if st == 200 and traintuples is not None:
            for traintuple in traintuples:
                # check if challenge exists and its metrics is not null
                challengeHash = traintuple['challenge']['hash']

                try:
                    # get challenge from local db
                    challenge = Challenge.objects.get(pk=challengeHash)
                except:
                    challenge = None
                finally:
                    if challenge is None or not challenge.metrics:
                        # get challenge metrics
                        try:
                            content, computed_hash = get_remote_file(traintuple['challenge']['metrics'])
                        except Exception as e:
                            logging.error(e, exc_info=True)
                            return fail(traintuple['key'], e)

                        challenge, created = Challenge.objects.update_or_create(pkhash=challengeHash, validated=True)

                        try:
                            f = tempfile.TemporaryFile()
                            f.write(content)
                            # update challenge in local db for later use
                            challenge.metrics.save('metrics.py', f)
                        except Exception as e:
                            logging.error(e, exc_info=True)
                            return fail(traintuple['key'], 'Failed to save challenge metrics in local db for later use')

                ''' get algo + model_type '''
                # get algo file
                try:
                    algo_content, algo_computed_hash = get_remote_file(traintuple['algo'])
                except Exception as e:
                    logging.error(e, exc_info=True)
                    return fail(traintuple['key'], e)

                # get model file
                if traintuple.get(model_type, None) is not None:
                    try:
                        model_content, model_computed_hash = get_remote_file(traintuple[model_type])
                    except Exception as e:
                        logging.error(e, exc_info=True)
                        return fail(traintuple['key'], e)

                # create a folder named traintuple['key'] im /medias/traintuple with 5 folders opener, data, model, pred, metrics
                traintuple_directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'traintuple/%s' % traintuple['key'])
                create_directory(traintuple_directory)
                for folder in ['opener', 'data', 'model', 'pred', 'metrics']:
                    create_directory(path.join(traintuple_directory, folder))

                # put opener file in opener folder
                try:
                    dataset = Dataset.objects.get(pk=traintuple[data_type]['openerHash'])
                except Exception as e:
                    logging.error(e, exc_info=True)
                    return fail(traintuple['key'], e)

                data_opener_hash = get_hash(dataset.data_opener.path)
                if data_opener_hash != traintuple[data_type]['openerHash']:
                    return fail(traintuple['key'], 'DataOpener Hash in Traintuple is not the same as in local db')
                copy(dataset.data_opener.path, path.join(traintuple_directory, 'opener'))

                # same for each train/test data
                for data_key in traintuple[data_type]['keys']:
                    try:
                        data = Data.objects.get(pk=data_key)
                    except Exception as e:
                        logging.error(e, exc_info=True)
                        return fail(traintuple['key'], e)
                    else:
                        data_hash = get_hash(data.file.path)
                        if data_hash != data_key:
                            return fail(traintuple['key'], 'Data Hash in Traintuple is not the same as in local db')

                        try:
                            to_directory = path.join(traintuple_directory, 'data')
                            copy(data.file.path, to_directory)
                            # unzip files
                            zip_file_path = os.path.join(to_directory, os.path.basename(data.file.name))
                            zip_ref = zipfile.ZipFile(zip_file_path, 'r')
                            zip_ref.extractall(to_directory)
                            zip_ref.close()
                            os.remove(zip_file_path)
                        except Exception as e:
                            logging.error(e, exc_info=True)
                            return fail(traintuple['key'], 'Fail to unzip data file')

                # same for model (can be null)
                if traintuple.get(model_type, None) is not None:
                    try:
                        model = Model.objects.get(pk=traintuple[model_type]['hash'])
                    except:  # get it from its address
                        model_path = path.join(traintuple_directory, 'model/model')
                        with open(model_path, 'wb') as f:
                            f.write(model_content)
                    else:
                        if get_hash(model.file.path) != traintuple[model_type]['hash']:
                            return fail(traintuple['key'], 'Model Hash in Traintuple is not the same as in local db')
                        os.link(model.file.path, path.join(traintuple_directory, 'model/model'))

                # put algo to root
                untar_algo(algo_content, traintuple_directory, traintuple)

                # same for challenge metrics
                os.link(challenge.metrics.path, path.join(traintuple_directory, 'metrics/metrics.py'))

                # do not put anything in pred folder

                # Log Start TrainTest with status_to_set
                data, st = invokeLedger({
                    'org': settings.LEDGER['org'],
                    'peer': settings.LEDGER['peer'],
                    'args': '{"Args":["logStartTrainTest","%s","%s"]}' % (traintuple['key'], status_to_set)
                })

                if st != 201:
                    logging.error('Failed to invoke ledger on prepareTask %s' % data_type, exc_info=True)
                else:
                    logging.info('Prepare Task success %s' % data_type)

                    try:
                        doTask.apply_async((traintuple, data_type), queue=settings.LEDGER['org']['name'])
                    except Exception as e:
                        logging.error(e, exc_info=True)
                        return fail(traintuple['key'], e)


@app.task
def prepareTrainingTask():
    prepareTask('trainData', 'trainWorker', 'todo', 'startModel', 'training')


@app.task
def prepareTestingTask():
    prepareTask('testData', 'testWorker', 'trained', 'endModel', 'testing')


@app.task
def doTask(traintuple, data_type):
    # data_type in ['trainData', 'testData']

    cpu_set = None
    gpu_set = None
    command = {'trainData': 'train',
               'testData': 'predict'}

    # compute
    try:
        from substrapp.models import Model
        # Log
        job_task_log = ''

        # Setup Docker Client
        client = docker.from_env()

        # Docker variables
        traintuple_root_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                                         'traintuple/%s/' % (traintuple['key']))
        algo_path = path.join(traintuple_root_path)
        algo_docker = ('algo_%s' % data_type).lower()    # tag must be lowercase for docker
        algo_docker_name = '%s_%s' % (algo_docker, traintuple['key'])
        metrics_docker = ('metrics_%s' % data_type).lower()    # tag must be lowercase for docker
        metrics_docker_name = '%s_%s' % (metrics_docker, traintuple['key'])
        model_path = os.path.join(traintuple_root_path, 'model')
        data_path = os.path.join(traintuple_root_path, 'data')
        pred_path = os.path.join(traintuple_root_path, 'pred')
        opener_file = os.path.join(traintuple_root_path, 'opener/opener.py')
        metrics_file = os.path.join(traintuple_root_path, 'metrics/metrics.py')

        # Build algo
        client.images.build(path=algo_path,
                            tag=algo_docker,
                            rm=True)

        # Run algo
        volumes = {data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
                   pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
                   model_path: {'bind': '/sandbox/model', 'mode': 'rw'},
                   opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

        mem_limit = ressource_manager.memory_limit_mb()

        while cpu_set is None or gpu_set is None:
            cpu_set = ressource_manager.acquire_cpu_set()
            gpu_set = ressource_manager.acquire_gpu_set()
            time.sleep(2)

        job_args = {'image': algo_docker,
                    'name': algo_docker_name,
                    'cpuset_cpus': cpu_set,
                    'mem_limit': mem_limit,
                    'command': command[data_type],
                    'volumes': volumes,
                    'detach': False,
                    'auto_remove': False,
                    'remove': False}

        if gpu_set != 'no_gpu':
            job_args['environment'] = {'NVIDIA_VISIBLE_DEVICES': gpu_set}
            job_args['runtime'] = 'nvidia'

        job = ExceptionThread(target=client.containers.run,
                              kwargs=job_args)
        monitoring = ExceptionThread(target=monitoring_job, args=(client, job_args))

        job.start()
        monitoring.start()

        job.join()
        monitoring.do_run = False
        monitoring.join()

        job_task_log = monitoring._result

        # Return ressources
        ressource_manager.return_cpu_set(cpu_set)
        ressource_manager.return_gpu_set(gpu_set)

        if hasattr(job, "_exception"):
            raise job._exception

        # Remove only if container exit without exception
        container = client.containers.get(algo_docker_name)
        container.remove()

        # Build metrics
        client.images.build(path=path.join(getattr(settings, 'PROJECT_ROOT'), 'base_metrics'),
                            tag=metrics_docker,
                            rm=True)

        # Compute metrics on train predictions
        volumes = {data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
                   pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
                   metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'},
                   opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

        cpu_set = None
        gpu_set = None
        mem_limit = ressource_manager.memory_limit_mb()

        while cpu_set is None or gpu_set is None:
            cpu_set = ressource_manager.acquire_cpu_set()
            gpu_set = ressource_manager.acquire_gpu_set()
            time.sleep(2)

        metrics_args = {'image': metrics_docker,
                        'name': metrics_docker_name,
                        'cpuset_cpus': cpu_set,
                        'mem_limit': mem_limit,
                        'volumes': volumes,
                        'detach': False,
                        'auto_remove': False,
                        'remove': False}

        if gpu_set != 'no_gpu':
            metrics_args['environment'] = {'NVIDIA_VISIBLE_DEVICES': gpu_set}
            metrics_args['runtime'] = 'nvidia'

        metric = ExceptionThread(target=client.containers.run,
                                 kwargs=metrics_args)
        monitoring = ExceptionThread(target=monitoring_job, args=(client, metrics_args))

        metric.start()
        monitoring.start()

        metric.join()
        monitoring.do_run = False
        monitoring.join()

        # Return ressources
        ressource_manager.return_cpu_set(cpu_set)
        ressource_manager.return_gpu_set(gpu_set)

        if hasattr(metric, "_exception"):
            raise metric._exception

        # Remove only if container exit without exception
        container = client.containers.get(metrics_docker_name)
        container.remove()

        if data_type == 'trainData':
            # Compute end model information
            end_model_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                                       'traintuple/%s/model/model' % (traintuple['key']))
            end_model_file_hash = get_hash(end_model_path)

            instance = Model.objects.create(pkhash=end_model_file_hash, validated=True)
            with open(end_model_path, 'rb') as f:
                instance.file.save('model', f)

            url_http = 'http' if settings.DEBUG else 'https'
            current_site = '%s:%s' % (getattr(settings, 'SITE_HOST'), getattr(settings, 'SITE_PORT'))
            end_model_file = '%s://%s%s' % (url_http, current_site, reverse('substrapp:model-file', args=[end_model_file_hash]))

        # Load performance
        with open(os.path.join(pred_path, 'perf.json'), 'r') as perf_file:
            perf = json.load(perf_file)
        global_perf = perf['all']

    except Exception as e:
        ressource_manager.return_cpu_set(cpu_set)
        ressource_manager.return_gpu_set(gpu_set)
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        return fail(traintuple['key'], error_code)

    # Put results in the Ledger
    if data_type == 'trainData':
        # Log Success Train
        data, st = invokeLedger({
            'org': settings.LEDGER['org'],
            'peer': settings.LEDGER['peer'],
            'args': '{"Args":["logSuccessTrain","%s","%s, %s","%s","Train - %s; "]}' % (traintuple['key'],
                                                                                        end_model_file_hash,
                                                                                        end_model_file,
                                                                                        global_perf,
                                                                                        job_task_log)
        })
    elif data_type == 'testData':
        # Log Success Test
        data, st = invokeLedger({
            'org': settings.LEDGER['org'],
            'peer': settings.LEDGER['peer'],
            'args': '{"Args":["logSuccessTest","%s","%s","Test - %s; "]}' % (traintuple['key'],
                                                                             global_perf,
                                                                             job_task_log)
        })

    return

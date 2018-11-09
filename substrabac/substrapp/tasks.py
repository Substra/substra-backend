from __future__ import absolute_import, unicode_literals

import os
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

    try:
        kwargs = {'auth': (getattr(settings, 'AUTH_USER'), getattr(settings, 'AUTH_PASSWORD')), 'verify': False}
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
    try:
        content, computed_hash = get_computed_hash(object['storageAddress'])  # TODO pass cert
    except Exception:
        raise Exception('Failed to fetch file')
    else:
        if computed_hash != object['hash']:
            msg = 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'
            raise Exception(msg)

        return content, computed_hash


def fail(key, err_msg):
    # Log Fail TrainTest
    data, st = invokeLedger({
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["logFailTrainTest","%(key)s","%(err_msg)s"]}' % {'key': key, 'err_msg': str(err_msg).replace('"', "'").replace('\\', "").replace('\\n', "")[:200]}
    })

    if st != 201:
        # TODO log error
        pass

    return data


def untar_algo(traintuple):
    try:
        content, computed_hash = get_remote_file(traintuple['algo'])
    except Exception as e:
        return fail(traintuple['key'], e)
    else:
        try:
            to_directory_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                                          'traintuple/%s' % (traintuple['key']))
            to_file_path = '%s/%s' % (to_directory_path, 'algo.tar.gz')
            os.makedirs(os.path.dirname(to_file_path), exist_ok=True)
            with open(to_file_path, 'wb') as f:
                f.write(content)

            tar = tarfile.open(to_file_path)
            tar.extractall(to_directory_path)
            tar.close()
            os.remove(to_file_path)
        except:
            return fail(traintuple['key'], 'Fail to untar algo file')


def untar_algo_from_local(algo, traintuple):
    from shutil import copy

    algo_file_hash = get_hash(algo.file.path)
    if algo_file_hash != traintuple['algo']['hash']:
        return fail(traintuple['key'], 'Algo Hash in Traintuple is not the same as in local db')

    try:
        to_directory_path = path.join(getattr(settings, 'MEDIA_ROOT'), 'traintuple/%s' % (traintuple['key']))

        # TODO update copy for supporting url
        copy(algo.file.path, to_directory_path)
        tar_file_path = os.path.join(to_directory_path, os.path.basename(algo.file.name))
        tar = tarfile.open(tar_file_path)
        tar.extractall(to_directory_path)
        tar.close()
        os.remove(tar_file_path)
    except:
        return fail(traintuple['key'], 'Fail to untar algo file')


def save_challenge(traintuple):
    try:
        content, computed_hash = get_remote_file(traintuple['challenge']['metrics'])
    except Exception as e:
        return fail(traintuple['key'], e)
    else:
        to_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                            'traintuple/%s/%s/%s' % (traintuple['key'], 'metrics', 'metrics.py'))
        os.makedirs(os.path.dirname(to_path), exist_ok=True)
        with open(to_path, 'wb') as f:
            f.write(content)


def save_challenge_from_local(challenge, traintuple):
    from shutil import copy
    challenge_metrics_hash = get_hash(challenge.metrics.path)
    if challenge_metrics_hash != traintuple['challenge']['metrics']['hash']:
        return fail(traintuple['key'], 'Challenge Hash in Traintuple is not the same as in local db')

    copy(challenge.metrics.path,
         path.join(getattr(settings, 'MEDIA_ROOT'),
                   'traintuple/%s/%s' % (traintuple['key'], 'metrics')))


def monitoring_job(client, train_args):
    """thread worker function"""

    job_name = train_args['name']

    gpu_set = None
    if 'environment' in train_args:
        gpu_set = train_args['environment']['NVIDIA_VISIBLE_DEVICES']

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
    __concurrency = int(os.environ.get('CELERYD_CONCURRENCY', 2))
    __memory_gb = int(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024.**2))

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
        pass
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
                    challenge = Challenge.objects.get(pk=challengeHash)
                except:
                    # get challenge metrics
                    try:
                        content, computed_hash = get_remote_file(traintuple['challenge']['metrics'])
                    except Exception as e:
                        logging.error(e)
                        return fail(traintuple['key'], e)
                    else:
                        try:
                            f = tempfile.TemporaryFile()
                            f.write(content)

                            # save/update challenge in local db for later use
                            instance, created = Challenge.objects.update_or_create(pkhash=challengeHash, validated=True)
                            instance.metrics.save('metrics.py', f)
                        except:
                            return fail(traintuple['key'], 'Failed to save challenge metrics in local db for later use')
                else:
                    if not challenge.metrics:
                        # get challenge metrics
                        try:
                            content, computed_hash = get_remote_file(traintuple['challenge']['metrics'])
                        except Exception as e:
                            return fail(traintuple['key'], e)
                        else:
                            try:
                                f = tempfile.TemporaryFile()
                                f.write(content)

                                # save/update challenge in local db for later use
                                instance, created = Challenge.objects.update_or_create(pkhash=challengeHash,
                                                                                       validated=True)
                                instance.metrics.save('metrics.py', f)
                            except:
                                return fail(traintuple['key'], 'Failed to save challenge metrics in local db for later use')

                ''' get algo + model_type '''
                # get algo file
                try:
                    get_remote_file(traintuple['algo'])
                except Exception as e:
                    return fail(traintuple['key'], e)

                # get model file
                try:
                    if traintuple[model_type] is not None:
                        get_remote_file(traintuple[model_type])
                except Exception as e:
                    return fail(traintuple['key'], e)

                # create a folder named traintuple['key'] im /medias/traintuple with 5 folders opener, data, model, pred, metrics
                directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'traintuple/%s' % traintuple['key'])
                create_directory(directory)
                folders = ['opener', 'data', 'model', 'pred', 'metrics']
                for folder in folders:
                    directory = path.join(getattr(settings, 'MEDIA_ROOT'),
                                          'traintuple/%s/%s' % (traintuple['key'], folder))
                    create_directory(directory)

                # put opener file in opener folder
                try:
                    dataset = Dataset.objects.get(pk=traintuple[data_type]['openerHash'])
                except Exception as e:
                    return fail(traintuple['key'], e)
                else:
                    data_opener_hash = get_hash(dataset.data_opener.path)
                    if data_opener_hash != traintuple[data_type]['openerHash']:
                        return fail(traintuple['key'], 'DataOpener Hash in Traintuple is not the same as in local db')

                    copy(dataset.data_opener.path,
                         path.join(getattr(settings, 'MEDIA_ROOT'), 'traintuple/%s/%s' % (traintuple['key'], 'opener')))

                # same for each train/test data
                for data_key in traintuple[data_type]['keys']:
                    try:
                        data = Data.objects.get(pk=data_key)
                    except Exception as e:
                        return fail(traintuple['key'], e)
                    else:
                        data_hash = get_hash(data.file.path)
                        if data_hash != data_key:
                            return fail(traintuple['key'],
                                        'Data Hash in Traintuple is not the same as in local db')

                        try:
                            to_directory = path.join(getattr(settings, 'MEDIA_ROOT'),
                                                     'traintuple/%s/%s' % (traintuple['key'], 'data'))
                            copy(data.file.path, to_directory)
                            # unzip files
                            zip_file_path = os.path.join(to_directory, os.path.basename(data.file.name))
                            zip_ref = zipfile.ZipFile(zip_file_path, 'r')
                            zip_ref.extractall(to_directory)
                            zip_ref.close()
                            os.remove(zip_file_path)
                        except:
                            return fail(traintuple['key'], 'Fail to unzip data file')

                # same for model (can be null)
                model = None
                try:
                    if traintuple[model_type] is not None:
                        model = Model.objects.get(pk=traintuple[model_type]['hash'])
                except Exception as e:  # get it from its address
                    try:
                        content, computed_hash = get_remote_file(traintuple[model_type])
                    except:
                        return fail(traintuple['key'], e)
                    else:
                        to_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                                            'traintuple/%s/%s/%s' % (traintuple['key'], 'model', 'model'))
                        os.makedirs(os.path.dirname(to_path), exist_ok=True)
                        with open(to_path, 'wb') as f:
                            f.write(content)
                else:
                    if model is not None:
                        model_file_hash = get_hash(model.file.path)
                        if model_file_hash != traintuple[model_type]['hash']:
                            return fail(traintuple['key'], 'Model Hash in Traintuple is not the same as in local db')

                        copy(model.file.path,
                             path.join(getattr(settings, 'MEDIA_ROOT'), 'traintuple/%s/%s' % (traintuple['key'], 'model')))

                # put algo to root
                try:
                    algo = Algo.objects.get(pk=traintuple['algo']['hash'])
                except Exception as e:  # get it from its address
                    untar_algo(traintuple)
                else:
                    if algo.file:
                        untar_algo_from_local(algo, traintuple)
                    else:  # fallback get it from its address
                        untar_algo(traintuple)

                # same for challenge metrics
                try:
                    challenge = Challenge.objects.get(pk=traintuple['challenge']['hash'])
                except Exception as e:
                    save_challenge(traintuple)
                else:
                    if challenge.metrics:
                        save_challenge_from_local(challenge, traintuple)
                    else:
                        save_challenge(traintuple)

                # do not put anything in pred folder

                # Log Start TrainTest with status_to_set
                data, st = invokeLedger({
                    'org': settings.LEDGER['org'],
                    'peer': settings.LEDGER['peer'],
                    'args': '{"Args":["logStartTrainTest","%s","%s"]}' % (traintuple['key'], status_to_set)
                })

                if st != 201:
                    # TODO log error
                    pass

                # TODO log success

                if data_type == 'trainData':
                    try:
                        doTrainingTask.apply_async((traintuple, ), queue=settings.LEDGER['org']['name'])
                    except Exception as e:
                        return fail(traintuple['key'], e)
                elif data_type == 'testData':
                    try:
                        doTestingTask.apply_async((traintuple, ), queue=settings.LEDGER['org']['name'])
                    except Exception as e:
                        return fail(traintuple['key'], e)


@app.task
def prepareTrainingTask():
    prepareTask('trainData', 'trainWorker', 'todo', 'startModel', 'training')


@app.task
def prepareTestingTask():
    prepareTask('testData', 'testWorker', 'trained', 'endModel', 'testing')


@app.task
def doTrainingTask(traintuple):
    cpu_set = None
    gpu_set = None

    try:
        from django.contrib.sites.models import Site
        from substrapp.models import Model

        # Log
        training_task_log = ''

        # Setup Docker Client
        client = docker.from_env()

        # Docker variables
        # Need to replace media root path if we have substrabac and celery worker in containers to refer to the host path
        media_root_path = getattr(settings, 'MEDIA_ROOT')
        project_root_path = getattr(settings, 'PROJECT_ROOT')

        traintuple_root_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                                         'traintuple/%s/' % (traintuple['key']))
        algo_path = path.join(traintuple_root_path)
        algo_docker = 'algo_train'
        algo_docker_name = 'algo_train_%s' % (traintuple['key'])
        metrics_docker = 'metrics_train'
        metrics_docker_name = 'metrics_train_%s' % (traintuple['key'])
        model_path = os.path.join(traintuple_root_path, 'model')
        train_data_path = os.path.join(traintuple_root_path, 'data')
        train_pred_path = os.path.join(traintuple_root_path, 'pred')
        opener_file = os.path.join(traintuple_root_path, 'opener/opener.py')
        metrics_file = os.path.join(traintuple_root_path, 'metrics/metrics.py')

        # Build algo
        client.images.build(path=algo_path,
                            tag=algo_docker,
                            rm=True)

        # Run algo, train and make train predictions
        # Need to replace media root path if we have substrabac and celery worker in containers to refer to the host path
        volumes = {train_data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
                   train_pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
                   model_path: {'bind': '/sandbox/model', 'mode': 'rw'},
                   opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

        mem_limit = ressource_manager.memory_limit_mb()

        while cpu_set is None or gpu_set is None:
            cpu_set = ressource_manager.acquire_cpu_set()
            gpu_set = ressource_manager.acquire_gpu_set()
            time.sleep(2)

        train_args = {'image': algo_docker,
                      'name': algo_docker_name,
                      'cpuset_cpus': cpu_set,
                      'mem_limit': mem_limit,
                      'command': 'train',
                      'volumes': volumes,
                      'detach': False,
                      'auto_remove': False,
                      'remove': False,
                      }

        if gpu_set != 'no_gpu':
            train_args['environment'] = {'NVIDIA_VISIBLE_DEVICES': gpu_set},
            train_args['runtime'] = 'nvidia',

        training = ExceptionThread(target=client.containers.run,
                                   kwargs=train_args)

        monitoring = ExceptionThread(target=monitoring_job, args=(client, train_args))

        training.start()
        monitoring.start()

        training.join()
        monitoring.do_run = False
        monitoring.join()

        training_task_log = monitoring._result

        # Return ressources
        ressource_manager.return_cpu_set(cpu_set)
        ressource_manager.return_gpu_set(gpu_set)

        if hasattr(training, "_exception"):
            raise training._exception

        # Remove only if container exit without exception
        container = client.containers.get(algo_docker_name)
        container.remove()

        # Build metrics
        client.images.build(path=path.join(getattr(settings, 'PROJECT_ROOT'), 'base_metrics'),
                            tag=metrics_docker,
                            rm=True)

        # Compute metrics on train predictions
        # Need to replace media root path if we have substrabac and celery worker in containers to refer to the host path
        volumes = {train_data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
                   train_pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
                   metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'},
                   opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

        mem_limit = ressource_manager.memory_limit_mb()
        cpu_set = None
        gpu_set = None

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
            metrics_args['environment'] = {'NVIDIA_VISIBLE_DEVICES': gpu_set},
            metrics_args['runtime'] = 'nvidia',

        metric = ExceptionThread(target=client.containers.run,
                                 kwargs=metrics_args)
        monitoring = ExceptionThread(target=monitoring_job, args=(client, metrics_args))

        metric.start()
        monitoring.start()

        metric.join()
        monitoring.do_run = False
        monitoring.join()

        ressource_manager.return_cpu_set(cpu_set)
        ressource_manager.return_gpu_set(gpu_set)

        if hasattr(metric, "_exception"):
            raise metric._exception

        # Remove only if container exit without exception
        container = client.containers.get(metrics_docker_name)
        container.remove()

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
        with open(os.path.join(train_pred_path, 'perf.json'), 'r') as perf_file:
            perf = json.load(perf_file)
        global_perf = perf['all']

    except Exception as e:
        ressource_manager.return_cpu_set(cpu_set)
        ressource_manager.return_gpu_set(gpu_set)
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        return fail(traintuple['key'], error_code)

    # Log Success Train
    data, st = invokeLedger({
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["logSuccessTrain","%s","%s, %s","%s","Train - %s; "]}' % (traintuple['key'],
                                                                                    end_model_file_hash,
                                                                                    end_model_file,
                                                                                    global_perf,
                                                                                    training_task_log)
    })

    return


@app.task
def doTestingTask(traintuple):
    try:
        # Log
        testing_task_log = ''

        # Setup Docker Client
        client = docker.from_env()

        # Docker variables
        # Need to replace media root path if we have substrabac and celery worker in containers to refer to the host path
        media_root_path = getattr(settings, 'MEDIA_ROOT')
        project_root_path = getattr(settings, 'PROJECT_ROOT')
        traintuple_root_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                                         'traintuple/%s/' % (traintuple['key']))
        algo_path = path.join(traintuple_root_path)
        algo_docker = 'algo_test'
        algo_docker_name = 'algo_test_%s' % (traintuple['key'])
        metrics_docker = 'metrics_test'
        metrics_docker_name = 'metrics_test_%s' % (traintuple['key'])
        model_path = os.path.join(traintuple_root_path, 'model')
        test_data_path = os.path.join(traintuple_root_path, 'data')
        test_pred_path = os.path.join(traintuple_root_path, 'pred')
        opener_file = os.path.join(traintuple_root_path, 'opener/opener.py')
        metrics_file = os.path.join(traintuple_root_path, 'metrics/metrics.py')

        # Build algo
        client.images.build(path=algo_path,
                            tag=algo_docker,
                            rm=True)

        # Run algo and make test predictions
        # Need to replace media root path if we have substrabac and celery worker in containers to refer to the host path
        volumes = {test_data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
                   test_pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
                   model_path: {'bind': '/sandbox/model', 'mode': 'rw'},
                   opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

        mem_limit = ressource_manager.memory_limit_mb()
        cpu_set = None
        gpu_set = None

        while cpu_set is None or gpu_set is None:
            cpu_set = ressource_manager.acquire_cpu_set()
            gpu_set = ressource_manager.acquire_gpu_set()
            time.sleep(2)

        testing_args = {'image': algo_docker,
                        'name': algo_docker_name,
                        'cpuset_cpus': cpu_set,
                        'mem_limit': mem_limit,
                        'command': 'predict',
                        'volumes': volumes,
                        'detach': False,
                        'auto_remove': False,
                        'remove': False}

        if gpu_set != 'no_gpu':
            testing_args['environment'] = {'NVIDIA_VISIBLE_DEVICES': gpu_set},
            testing_args['runtime'] = 'nvidia',

        testing = ExceptionThread(target=client.containers.run,
                                  kwargs=testing_args)
        monitoring = ExceptionThread(target=monitoring_job, args=(client, testing_args))

        testing.start()
        monitoring.start()

        testing.join()
        monitoring.do_run = False
        monitoring.join()

        testing_task_log = monitoring._result

        ressource_manager.return_cpu_set(cpu_set)
        ressource_manager.return_gpu_set(gpu_set)

        if hasattr(testing, "_exception"):
            raise testing._exception

        # Remove only if container exit without exception
        container = client.containers.get(algo_docker_name)
        container.remove()

        # Build metrics
        client.images.build(path=path.join(getattr(settings, 'PROJECT_ROOT'), 'base_metrics'),
                            tag=metrics_docker,
                            rm=True)

        # Compute metrics on train predictions
        # Need to replace media root path if we have substrabac and celery worker in containers to refer to the host path
        volumes = {test_data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
                   test_pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
                   metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'},
                   opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

        mem_limit = ressource_manager.memory_limit_mb()
        cpu_set = None
        gpu_set = None

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
            metrics_args['environment'] = {'NVIDIA_VISIBLE_DEVICES': gpu_set},
            metrics_args['runtime'] = 'nvidia',

        metric = ExceptionThread(target=client.containers.run,
                                 kwargs=metrics_args)
        monitoring = ExceptionThread(target=monitoring_job, args=(client, metrics_args))

        metric.start()
        monitoring.start()

        metric.join()
        monitoring.do_run = False
        monitoring.join()

        ressource_manager.return_cpu_set(cpu_set)
        ressource_manager.return_gpu_set(gpu_set)

        if hasattr(testing, "_exception"):
            raise testing._exception

        # Remove only if container exit without exception
        container = client.containers.get(metrics_docker_name)
        container.remove()

        # Load performance
        with open(os.path.join(test_pred_path, 'perf.json'), 'r') as perf_file:
            perf = json.load(perf_file)
        global_perf = perf['all']

    except Exception as e:
        ressource_manager.return_cpu_set(cpu_set)
        ressource_manager.return_gpu_set(gpu_set)
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        return fail(traintuple['key'], error_code)

    # Log Success Test
    data, st = invokeLedger({
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["logSuccessTest","%s","%s","Test - %s; "]}' % (traintuple['key'],
                                                                         global_perf,
                                                                         testing_task_log)
    })

    return

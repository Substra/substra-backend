from __future__ import absolute_import, unicode_literals

import os
import shutil
import tempfile
from os import path

from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse

from substrabac.celery import app
from substrapp.utils import queryLedger, invokeLedger
from substrapp.utils import get_hash, untar_algo, create_directory, get_remote_file
from substrapp.job_utils import ResourcesManager, compute_docker
from substrapp.exception_handler import compute_error_code

import docker
import json
from multiprocessing.managers import BaseManager

import logging


def get_challenge(traintuple):
    from substrapp.models import Challenge

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
                raise e

            challenge, created = Challenge.objects.update_or_create(pkhash=challengeHash, validated=True)

            try:
                f = tempfile.TemporaryFile()
                f.write(content)
                challenge.metrics.save('metrics.py', f)  # update challenge in local db for later use
            except Exception as e:
                logging.error('Failed to save challenge metrics in local db for later use')
                raise e

    return challenge


def get_algo(traintuple):
    algo_content, algo_computed_hash = get_remote_file(traintuple['algo'])
    return algo_content, algo_computed_hash


def get_model(traintuple, model_type):
    model_content, model_computed_hash = None, None

    if traintuple.get(model_type, None) is not None:
        model_content, model_computed_hash = get_remote_file(traintuple[model_type])

    return model_content, model_computed_hash


def put_model(traintuple, traintuple_directory, model_content, model_type):
    if model_content is not None:
        from substrapp.models import Model

        model_dst_path = path.join(traintuple_directory, 'model/model')

        try:
            model = Model.objects.get(pk=traintuple[model_type]['hash'])
        except:  # write it to local disk
            with open(model_dst_path, 'wb') as f:
                f.write(model_content)
        else:
            if get_hash(model.file.path) != traintuple[model_type]['hash']:
                raise Exception('Model Hash in Traintuple is not the same as in local db')

            if not os.path.exists(model_dst_path):
                os.link(model.file.path, model_dst_path)
            else:
                if get_hash(model_dst_path) != traintuple[model_type]['hash']:
                    raise Exception('Model Hash in Traintuple is not the same as in local medias')


def put_opener(traintuple, traintuple_directory, data_type):
    from substrapp.models import Dataset

    try:
        dataset = Dataset.objects.get(pk=traintuple[data_type]['openerHash'])
    except Exception as e:
        raise e

    data_opener_hash = get_hash(dataset.data_opener.path)
    if data_opener_hash != traintuple[data_type]['openerHash']:
        raise Exception('DataOpener Hash in Traintuple is not the same as in local db')

    opener_dst_path = path.join(traintuple_directory, 'opener/opener.py')
    if not os.path.exists(opener_dst_path):
        os.link(dataset.data_opener.path, opener_dst_path)


def put_data(traintuple, traintuple_directory, data_type):
    from shutil import copy
    from substrapp.models import Data
    import zipfile

    for data_key in traintuple[data_type]['keys']:
        try:
            data = Data.objects.get(pk=data_key)
        except Exception as e:
            raise e
        else:
            data_hash = get_hash(data.file.path)
            if data_hash != data_key:
                raise Exception('Data Hash in Traintuple is not the same as in local db')

            try:
                to_directory = path.join(traintuple_directory, 'data')
                copy(data.file.path, to_directory)
                # unzip files
                zip_file_path = path.join(to_directory, os.path.basename(data.file.name))
                zip_ref = zipfile.ZipFile(zip_file_path, 'r')
                zip_ref.extractall(to_directory)
                zip_ref.close()
                os.remove(zip_file_path)
            except Exception as e:
                logging.error('Fail to unzip data file')
                raise e


def put_metric(traintuple_directory, challenge):
    metrics_dst_path = path.join(traintuple_directory, 'metrics/metrics.py')
    if not os.path.exists(metrics_dst_path):
        os.link(challenge.metrics.path, metrics_dst_path)


def put_algo(traintuple, traintuple_directory, algo_content):
    try:
        untar_algo(algo_content, traintuple_directory, traintuple)
    except Exception as e:
        logging.error('Fail to untar algo file')
        raise e


def build_traintuple_folders(traintuple):
    # create a folder named traintuple['key'] im /medias/traintuple with 5 folders opener, data, model, pred, metrics
    traintuple_directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'traintuple', traintuple['key'])
    create_directory(traintuple_directory)
    for folder in ['opener', 'data', 'model', 'pred', 'metrics']:
        create_directory(path.join(traintuple_directory, folder))

    return traintuple_directory


def remove_traintuple_materials(traintuple_directory):
    try:
        shutil.rmtree(traintuple_directory)
    except Exception as e:
        logging.error(e)


def fail(key, err_msg):
    # Log Fail TrainTest
    err_msg = str(err_msg).replace('"', "'").replace('\\', "").replace('\\n', "")[:200]
    data, st = invokeLedger({
        'args': f'{{"Args":["logFailTrainTest","{key}","{err_msg}"]}}'
    }, sync=True)

    if st is not status.HTTP_201_CREATED:
        logging.error(data, exc_info=True)

    logging.info('Successfully passed the traintuple to failed')
    return data


# Instatiate Ressource Manager in BaseManager to share it between celery concurrent tasks
BaseManager.register('ResourcesManager', ResourcesManager)
manager = BaseManager()
manager.start()
resources_manager = manager.ResourcesManager()


def prepareTask(data_type, worker_to_filter, status_to_filter, model_type, status_to_set):
    from django_celery_results.models import TaskResult

    try:
        data_owner = get_hash(settings.LEDGER['signcert'])
    except Exception as e:
        logging.error(e, exc_info=True)
    else:
        traintuples, st = queryLedger({
            'args': f'{{"Args":["queryFilter","traintuple~{worker_to_filter}~status","{data_owner},{status_to_filter}"]}}'
        })

        if st == 200 and traintuples is not None:
            for traintuple in traintuples:

                fltask = None
                worker_queue = f"{settings.LEDGER['org']['name']}.worker"

                if 'FLtask' in traintuple:
                    fltask = traintuple['FLtask']
                    flresults = TaskResult.objects.filter(task_name='substrapp.tasks.computeTask',
                                                          result__icontains=f'"FLtask": "{fltask}"')

                    if flresults and flresults.count() > 0:
                        worker_queue = json.loads(flresults.first().as_dict()['result'])['worker']

                try:
                    computeTask.apply_async((traintuple, data_type, model_type, status_to_set, fltask),
                                            queue=worker_queue)
                except Exception as e:
                    error_code = compute_error_code(e)
                    logging.error(error_code, exc_info=True)
                    return fail(traintuple['key'], error_code)


@app.task(bind=True, ignore_result=True)
def prepareTrainingTask(self):
    prepareTask('trainData', 'trainWorker', 'todo', 'startModel', 'training')


@app.task(ignore_result=True)
def prepareTestingTask():
    prepareTask('testData', 'testWorker', 'trained', 'endModel', 'testing')


@app.task(bind=True, ignore_result=False)
def computeTask(self, traintuple, data_type, model_type, status_to_set, fltask):

    worker = self.request.hostname.split('@')[1]
    queue = self.request.delivery_info['routing_key']
    result = {'worker': worker, 'queue': queue, 'FLtask': fltask}

    # Get materials
    try:
        prepareMaterials(traintuple, data_type, model_type)
    except Exception as e:
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        fail(traintuple['key'], error_code)
        return result

    # Log Start TrainTest with status_to_set
    data, st = invokeLedger({
        'args': f'{{"Args":["logStartTrainTest","{traintuple["key"]}","{status_to_set}"]}}'
    }, sync=True)

    if st is not status.HTTP_201_CREATED:
        logging.error(f'Failed to invoke ledger on prepareTask {data_type}')
    else:
        logging.info(f'Prepare Task success {data_type}')

        try:
            res = doTask(traintuple, data_type)
        except Exception as e:
            error_code = compute_error_code(e)
            logging.error(error_code, exc_info=True)
            fail(traintuple['key'], error_code)
            return result
        else:
            # Invoke ledger to log success
            if data_type == 'trainData':
                invoke_args = f'{{"Args":["logSuccessTrain","{traintuple["key"]}", "{res["end_model_file_hash"]}, {res["end_model_file"]}","{res["global_perf"]}","Train - {res["job_task_log"]}; "]}}'
            elif data_type == 'testData':
                invoke_args = f'{{"Args":["logSuccessTest","{traintuple["key"]}","{res["global_perf"]}","Test - {res["job_task_log"]}; "]}}'

            data, st = invokeLedger({
                'args': invoke_args
            }, sync=True)

            if st is not status.HTTP_201_CREATED:
                logging.error('Failed to invoke ledger on logSuccess')
                logging.error(data)

    return result


def prepareMaterials(traintuple, data_type, model_type):
    # get traintuple components
    try:
        challenge = get_challenge(traintuple)
        algo_content, algo_computed_hash = get_algo(traintuple)
        model_content, model_computed_hash = get_model(traintuple, model_type)  # can return None, None
    except Exception as e:
        raise e

    # create traintuple
    try:
        traintuple_directory = build_traintuple_folders(traintuple)  # do not put anything in pred folder
        put_opener(traintuple, traintuple_directory, data_type)
        put_data(traintuple, traintuple_directory, data_type)
        put_metric(traintuple_directory, challenge)
        put_algo(traintuple, traintuple_directory, algo_content)
        put_model(traintuple, traintuple_directory, model_content, model_type)
    except Exception as e:
        raise e


def doTask(traintuple, data_type):
    # Must be defined before to return ressource in case of failure
    cpu_set = None
    gpu_set = None
    traintuple_directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'traintuple', traintuple['key'])

    # Federated learning variables
    fltask = 'test-fltask'
    flrank = 0

    if 'FLtask' in traintuple:
        fltask = traintuple['FLtask']
        flrank = int(traintuple['rank'])

    # Computation
    try:
        # Job log
        job_task_log = ''

        # Setup Docker Client
        client = docker.from_env()

        # traintuple setup
        model_path = path.join(traintuple_directory, 'model')
        data_path = path.join(traintuple_directory, 'data')
        pred_path = path.join(traintuple_directory, 'pred')
        opener_file = path.join(traintuple_directory, 'opener/opener.py')
        metrics_file = path.join(traintuple_directory, 'metrics/metrics.py')
        volumes = {data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
                   pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
                   metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'},
                   opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

        # compute algo task
        algo_path = path.join(traintuple_directory)
        algo_docker = f'algo_{data_type}'.lower()  # tag must be lowercase for docker
        algo_docker_name = f'{algo_docker}_{traintuple["key"]}'
        model_volume = {model_path: {'bind': '/sandbox/model', 'mode': 'rw'}}
        algo_command = 'train' if data_type == 'trainData' else 'predict' if data_type == 'testData' else None

        # local volume for fltask
        if fltask is not None and data_type == 'trainData':
            flvolume = f'local-{fltask}'
            if flrank == 0:
                client.volumes.create(name=flvolume)
            else:
                client.volumes.get(volume_id=flvolume)

            model_volume[flvolume] = {'bind': '/sandbox/local', 'mode': 'rw'}

        job_task_log = compute_docker(client=client,
                                      resources_manager=resources_manager,
                                      dockerfile_path=algo_path,
                                      image_name=algo_docker,
                                      container_name=algo_docker_name,
                                      volumes={**volumes, **model_volume},
                                      command=algo_command,
                                      cpu_set=cpu_set,
                                      gpu_set=gpu_set)
        # save model in database
        if data_type == 'trainData':
            from substrapp.models import Model
            end_model_path = path.join(traintuple_directory, 'model/model')
            end_model_file_hash = get_hash(end_model_path)
            instance = Model.objects.create(pkhash=end_model_file_hash, validated=True)
            with open(end_model_path, 'rb') as f:
                instance.file.save('model', f)
            url_http = 'http' if settings.DEBUG else 'https'
            current_site = f'{getattr(settings, "SITE_HOST")}:{getattr(settings, "SITE_PORT")}'
            end_model_file = f'{url_http}://{current_site}{reverse("substrapp:model-file", args=[end_model_file_hash])}'

        # compute metric task
        metrics_path = path.join(getattr(settings, 'PROJECT_ROOT'), 'base_metrics')   # base metrics comes with substrabac
        metrics_docker = f'metrics_{data_type}'.lower()  # tag must be lowercase for docker
        metrics_docker_name = f'{metrics_docker}_{traintuple["key"]}'
        metric_volume = {metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'}}
        compute_docker(client=client,
                       resources_manager=resources_manager,
                       dockerfile_path=metrics_path,
                       image_name=metrics_docker,
                       container_name=metrics_docker_name,
                       volumes={**volumes, **metric_volume},
                       command=None,
                       cpu_set=cpu_set,
                       gpu_set=gpu_set)

        # load performance
        with open(path.join(pred_path, 'perf.json'), 'r') as perf_file:
            perf = json.load(perf_file)
        global_perf = perf['all']

    except Exception as e:
        resources_manager.return_cpu_set(cpu_set)
        resources_manager.return_gpu_set(gpu_set)

        # If an exception is thrown set flrank == -1 (we stop the fl training)
        if fltask is not None:
            flrank = -1

        raise e
    else:
        result = {'global_perf': global_perf,
                  'job_task_log': job_task_log}

        if data_type == 'trainData':
            result['end_model_file_hash'] = end_model_file_hash
            result['end_model_file'] = end_model_file

    finally:
        # Clean traintuple materials
        remove_traintuple_materials(traintuple_directory)

        # Rank == -1 -> Last fl traintuple or fl throws an exception
        if flrank == -1:
            local_volume = client.volumes.get(volume_id=f'local-{fltask}')
            try:
                local_volume.remove(force=True)
            except:
                logging.error('Cannot remove local volume local-{fltask}', exc_info=True)

    return result

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


def get_challenge(subtuple):
    from substrapp.models import Challenge

    # check if challenge exists and its metrics is not null
    challengeHash = subtuple['challenge']['hash']

    try:
        # get challenge from local db
        challenge = Challenge.objects.get(pk=challengeHash)
    except:
        challenge = None
    finally:
        if challenge is None or not challenge.metrics:
            # get challenge metrics
            try:
                content, computed_hash = get_remote_file(subtuple['challenge']['metrics'])
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


def get_algo(subtuple):
    algo_content, algo_computed_hash = get_remote_file(subtuple['algo'])
    return algo_content, algo_computed_hash


def get_model(subtuple):
    model_content, model_computed_hash = None, None

    if subtuple.get('model', None) is not None:
        model_content, model_computed_hash = get_remote_file(subtuple['model'])

    return model_content, model_computed_hash


def get_models(subtuple):
    models_content, models_computed_hash = [], []

    if subtuple.get('inModels', None) is not None:
        for subtuple_model in subtuple['inModels']:
            model_content, model_computed_hash = get_remote_file(subtuple_model)
            models_content.append(model_content)
            models_computed_hash.append(model_computed_hash)

    return models_content, models_computed_hash


def put_model(subtuple, subtuple_directory, model_content):
    if model_content is not None:
        from substrapp.models import Model

        model_dst_path = path.join(subtuple_directory, f'model/{subtuple["model"]["traintupleKey"]}')

        try:
            model = Model.objects.get(pk=subtuple['model']['hash'])
        except:  # write it to local disk
            with open(model_dst_path, 'wb') as f:
                f.write(model_content)
        else:
            if get_hash(model.file.path) != subtuple['model']['hash']:
                raise Exception('Model Hash in Subtuple is not the same as in local db')

            if not os.path.exists(model_dst_path):
                os.link(model.file.path, model_dst_path)
            else:
                if get_hash(model_dst_path) != subtuple['model']['hash']:
                    raise Exception('Model Hash in Subtuple is not the same as in local medias')


def put_models(subtuple, subtuple_directory, models_content):
    if models_content:
        from substrapp.models import Model

        for model_content, subtuple_model in zip(models_content, subtuple['inModels']):
            model_dst_path = path.join(subtuple_directory, f'model/{subtuple_model["traintupleKey"]}')

            try:
                model = Model.objects.get(pk=subtuple_model['hash'])
            except:  # write it to local disk
                with open(model_dst_path, 'wb') as f:
                    f.write(model_content)
            else:
                if get_hash(model.file.path) != subtuple_model['hash']:
                    raise Exception('Model Hash in Subtuple is not the same as in local db')

                if not os.path.exists(model_dst_path):
                    os.link(model.file.path, model_dst_path)
                else:
                    if get_hash(model_dst_path) != subtuple_model['hash']:
                        raise Exception('Model Hash in Subtuple is not the same as in local medias')


def put_opener(subtuple, subtuple_directory):
    from substrapp.models import Dataset

    try:
        dataset = Dataset.objects.get(pk=subtuple['data']['openerHash'])
    except Exception as e:
        raise e

    data_opener_hash = get_hash(dataset.data_opener.path)
    if data_opener_hash != subtuple['data']['openerHash']:
        raise Exception('DataOpener Hash in Subtuple is not the same as in local db')

    opener_dst_path = path.join(subtuple_directory, 'opener/opener.py')
    if not os.path.exists(opener_dst_path):
        os.link(dataset.data_opener.path, opener_dst_path)


def put_data(subtuple, subtuple_directory):
    from shutil import copy
    from substrapp.models import Data
    import zipfile

    for data_key in subtuple['data']['keys']:
        try:
            data = Data.objects.get(pk=data_key)
        except Exception as e:
            raise e
        else:
            data_hash = get_hash(data.file.path)
            if data_hash != data_key:
                raise Exception('Data Hash in Subtuple is not the same as in local db')

            try:
                to_directory = path.join(subtuple_directory, 'data')
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


def put_metric(subtuple_directory, challenge):
    metrics_dst_path = path.join(subtuple_directory, 'metrics/metrics.py')
    if not os.path.exists(metrics_dst_path):
        os.link(challenge.metrics.path, metrics_dst_path)


def put_algo(subtuple, subtuple_directory, algo_content):
    try:
        untar_algo(algo_content, subtuple_directory, subtuple)
    except Exception as e:
        logging.error('Fail to untar algo file')
        raise e


def build_subtuple_folders(subtuple):
    # create a folder named subtuple['key'] im /medias/subtuple with 5 folders opener, data, model, pred, metrics
    subtuple_directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'subtuple', subtuple['key'])
    create_directory(subtuple_directory)
    for folder in ['opener', 'data', 'model', 'pred', 'metrics']:
        create_directory(path.join(subtuple_directory, folder))

    return subtuple_directory


def remove_subtuple_materials(subtuple_directory):
    try:
        shutil.rmtree(subtuple_directory)
    except Exception as e:
        logging.error(e)


def fail(key, err_msg, tuple_type):
    # Log Fail TrainTest
    err_msg = str(err_msg).replace('"', "'").replace('\\', "").replace('\\n', "")[:200]
    fail_type = 'logFailTrain' if tuple_type == 'traintuple' else 'logFailTest'
    data, st = invokeLedger({
        'args': f'{{"Args":["{fail_type}","{key}","{err_msg}"]}}'
    }, sync=True)

    if st is not status.HTTP_201_CREATED:
        logging.error(data, exc_info=True)

    logging.info('Successfully passed the subtuple to failed')
    return data


# Instatiate Ressource Manager in BaseManager to share it between celery concurrent tasks
BaseManager.register('ResourcesManager', ResourcesManager)
manager = BaseManager()
manager.start()
resources_manager = manager.ResourcesManager()


def prepareTask(tuple_type, model_type):
    from django_celery_results.models import TaskResult

    try:
        data_owner = get_hash(settings.LEDGER['signcert'])
    except Exception as e:
        logging.error(e, exc_info=True)
    else:
        subtuples, st = queryLedger({
            'args': f'{{"Args":["queryFilter","{tuple_type}~worker~status","{data_owner},todo"]}}'
        })

        if st == 200 and subtuples is not None:
            for subtuple in subtuples:

                fltask = None
                worker_queue = f"{settings.LEDGER['org']['name']}.worker"

                if 'fltask' in subtuple and subtuple['fltask']:
                    fltask = subtuple['fltask']
                    flresults = TaskResult.objects.filter(task_name='substrapp.tasks.computeTask',
                                                          result__icontains=f'"fltask": "{fltask}"')

                    if flresults and flresults.count() > 0:
                        worker_queue = json.loads(flresults.first().as_dict()['result'])['worker']

                try:
                    computeTask.apply_async((tuple_type, subtuple, model_type, fltask),
                                            queue=worker_queue)
                except Exception as e:
                    error_code = compute_error_code(e)
                    logging.error(error_code, exc_info=True)
                    return fail(subtuple['key'], error_code, tuple_type)


@app.task(bind=True, ignore_result=True)
def prepareTrainingTask(self):
    prepareTask('traintuple', 'inModels')


@app.task(ignore_result=True)
def prepareTestingTask():
    prepareTask('testtuple', 'model')


@app.task(bind=True, ignore_result=False)
def computeTask(self, tuple_type, subtuple, model_type, fltask):

    try:
        worker = self.request.hostname.split('@')[1]
        queue = self.request.delivery_info['routing_key']
    except:
        worker = f"{settings.LEDGER['org']['name']}.worker"
        queue = f"{settings.LEDGER['org']['name']}"

    result = {'worker': worker, 'queue': queue, 'fltask': fltask}

    # Get materials
    try:
        prepareMaterials(subtuple, model_type)
    except Exception as e:
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        fail(subtuple['key'], error_code, tuple_type)
        return result

    # Log Start of the Subtuple
    start_type = 'logStartTrain' if tuple_type == 'traintuple' else 'logStartTest' if tuple_type == 'testtuple' else None

    data, st = invokeLedger({
        'args': f'{{"Args":["{start_type}","{subtuple["key"]}"]}}'
    }, sync=True)

    if st is not status.HTTP_201_CREATED:
        logging.error(f'Failed to invoke ledger on prepareTask {tuple_type}')
    else:
        logging.info(f'Prepare Task success {tuple_type}')

        try:
            res = doTask(subtuple, tuple_type)
        except Exception as e:
            error_code = compute_error_code(e)
            logging.error(error_code, exc_info=True)
            fail(subtuple['key'], error_code, tuple_type)
            return result
        else:
            # Invoke ledger to log success
            if tuple_type == 'traintuple':
                invoke_args = f'{{"Args":["logSuccessTrain","{subtuple["key"]}", "{res["end_model_file_hash"]}, {res["end_model_file"]}","{res["global_perf"]}","Train - {res["job_task_log"]}; "]}}'
            elif tuple_type == 'testtuple':
                invoke_args = f'{{"Args":["logSuccessTest","{subtuple["key"]}","{res["global_perf"]}","Test - {res["job_task_log"]}; "]}}'

            data, st = invokeLedger({
                'args': invoke_args
            }, sync=True)

            if st is not status.HTTP_201_CREATED:
                logging.error('Failed to invoke ledger on logSuccess')
                logging.error(data)

    return result


def prepareMaterials(subtuple, model_type):
    # get subtuple components
    try:
        challenge = get_challenge(subtuple)
        algo_content, algo_computed_hash = get_algo(subtuple)
        if model_type == 'model':
            model_content, model_computed_hash = get_model(subtuple)  # can return None, None
        if model_type == 'inModels':
            models_content, models_computed_hash = get_models(subtuple)  # can return [], []

    except Exception as e:
        raise e

    # create subtuple
    try:
        subtuple_directory = build_subtuple_folders(subtuple)  # do not put anything in pred folder
        put_opener(subtuple, subtuple_directory)
        put_data(subtuple, subtuple_directory)
        put_metric(subtuple_directory, challenge)
        put_algo(subtuple, subtuple_directory, algo_content)
        if model_type == 'model':  # testtuple
            put_model(subtuple, subtuple_directory, model_content)
        if model_type == 'inModels':  # traintuple
            put_models(subtuple, subtuple_directory, models_content)

    except Exception as e:
        raise e


def doTask(subtuple, tuple_type):
    # Must be defined before to return ressource in case of failure
    cpu_set = None
    gpu_set = None
    subtuple_directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'subtuple', subtuple['key'])

    # Federated learning variables
    fltask = None
    flrank = None

    if 'fltask' in subtuple and subtuple['fltask']:
        fltask = subtuple['fltask']
        flrank = int(subtuple['rank'])

    # Computation
    try:
        # Job log
        job_task_log = ''

        # Setup Docker Client
        client = docker.from_env()

        # subtuple setup
        model_path = path.join(subtuple_directory, 'model')
        data_path = path.join(subtuple_directory, 'data')
        pred_path = path.join(subtuple_directory, 'pred')
        opener_file = path.join(subtuple_directory, 'opener/opener.py')
        metrics_file = path.join(subtuple_directory, 'metrics/metrics.py')
        volumes = {data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
                   pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
                   metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'},
                   opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

        # compute algo task
        algo_path = path.join(subtuple_directory)
        algo_docker = f'algo_{tuple_type}'.lower()  # tag must be lowercase for docker
        algo_docker_name = f'{algo_docker}_{subtuple["key"]}'
        model_volume = {model_path: {'bind': '/sandbox/model', 'mode': 'rw'}}

        if fltask is not None and flrank != -1:
            remove_image = False
        else:
            remove_image = True

        # create the command option for algo
        if tuple_type == 'traintuple':
            algo_command = '--train'    # main command

            # add list of inmodels
            if subtuple['inModels'] is not None:
                inmodels = [subtuple_model["traintupleKey"] for subtuple_model in subtuple['inModels']]
                algo_command += f' --inmodels {" ".join(inmodels)}'

            # add fltask rank for training
            if flrank is not None:
                algo_command += f' --rank {flrank}'

        elif tuple_type == 'testtuple':
            algo_command = '--predict'    # main command

            inmodels = subtuple['model']["traintupleKey"]
            algo_command += f' --inmodels {inmodels}'

        # local volume for fltask
        if fltask is not None and tuple_type == 'traintuple':
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
                                      gpu_set=gpu_set,
                                      remove_image=remove_image)
        # save model in database
        if tuple_type == 'traintuple':
            from substrapp.models import Model
            end_model_path = path.join(subtuple_directory, 'model/model')
            end_model_file_hash = get_hash(end_model_path)
            instance = Model.objects.create(pkhash=end_model_file_hash, validated=True)
            with open(end_model_path, 'rb') as f:
                instance.file.save('model', f)
            url_http = 'http' if settings.DEBUG else 'https'
            current_site = f'{getattr(settings, "SITE_HOST")}:{getattr(settings, "SITE_PORT")}'
            end_model_file = f'{url_http}://{current_site}{reverse("substrapp:model-file", args=[end_model_file_hash])}'

        # compute metric task
        metrics_path = path.join(getattr(settings, 'PROJECT_ROOT'), 'base_metrics')   # base metrics comes with substrabac
        metrics_docker = f'metrics_{tuple_type}'.lower()  # tag must be lowercase for docker
        metrics_docker_name = f'{metrics_docker}_{subtuple["key"]}'
        metric_volume = {metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'}}
        compute_docker(client=client,
                       resources_manager=resources_manager,
                       dockerfile_path=metrics_path,
                       image_name=metrics_docker,
                       container_name=metrics_docker_name,
                       volumes={**volumes, **metric_volume},
                       command=None,
                       cpu_set=cpu_set,
                       gpu_set=gpu_set,
                       remove_image=remove_image)

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

        if tuple_type == 'traintuple':
            result['end_model_file_hash'] = end_model_file_hash
            result['end_model_file'] = end_model_file

    finally:
        # Clean subtuple materials
        remove_subtuple_materials(subtuple_directory)

        # Rank == -1 -> Last fl subtuple or fl throws an exception
        if flrank == -1:
            flvolume = f'local-{fltask}'
            local_volume = client.volumes.get(volume_id=flvolume)
            try:
                local_volume.remove(force=True)
            except:
                logging.error(f'Cannot remove local volume {flvolume}', exc_info=True)

    return result

from __future__ import absolute_import, unicode_literals

import os
import shutil
import tempfile
from os import path

from checksumdir import dirhash
from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse

from substrabac.celery import app
from substrapp.utils import queryLedger, invokeLedger, get_hash, create_directory, get_remote_file, uncompress_content
from substrapp.task_utils import ResourcesManager, compute_docker
from substrapp.exception_handler import compute_error_code

import docker
import json
from multiprocessing.managers import BaseManager

import logging


def get_objective(subtuple):
    from substrapp.models import Objective

    # check if objective exists and its metrics is not null
    objectiveHash = subtuple['objective']['hash']

    try:
        # get objective from local db
        objective = Objective.objects.get(pk=objectiveHash)
    except:
        objective = None
    finally:
        if objective is None or not objective.metrics:
            # get objective metrics
            try:
                content, computed_hash = get_remote_file(subtuple['objective']['metrics'])
            except Exception as e:
                raise e

            objective, created = Objective.objects.update_or_create(pkhash=objectiveHash, validated=True)

            try:
                f = tempfile.TemporaryFile()
                f.write(content)
                objective.metrics.save('metrics.py', f)  # update objective in local db for later use
            except Exception as e:
                logging.error('Failed to save objective metrics in local db for later use')
                raise e

    return objective


def get_algo(subtuple):
    algo_content, algo_computed_hash = get_remote_file(subtuple['algo'])
    return algo_content, algo_computed_hash


def get_model(subtuple):
    model_content, model_computed_hash = None, None

    if subtuple.get('model', None) is not None:
        model_content, model_computed_hash = get_remote_file(subtuple['model'], subtuple['model']['traintupleKey'])

    return model_content, model_computed_hash


def get_models(subtuple):
    models_content, models_computed_hash = [], []

    if subtuple.get('inModels', None) is not None:
        for subtuple_model in subtuple['inModels']:
            model_content, model_computed_hash = get_remote_file(subtuple_model, subtuple_model['traintupleKey'])
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
            if get_hash(model.file.path, subtuple["model"]["traintupleKey"]) != subtuple['model']['hash']:
                raise Exception('Model Hash in Subtuple is not the same as in local db')

            if not os.path.exists(model_dst_path):
                os.link(model.file.path, model_dst_path)
            else:
                if get_hash(model_dst_path, subtuple["model"]["traintupleKey"]) != subtuple['model']['hash']:
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
                if get_hash(model.file.path, subtuple_model["traintupleKey"]) != subtuple_model['hash']:
                    raise Exception('Model Hash in Subtuple is not the same as in local db')

                if not os.path.exists(model_dst_path):
                    os.link(model.file.path, model_dst_path)
                else:
                    if get_hash(model_dst_path, subtuple_model["traintupleKey"]) != subtuple_model['hash']:
                        raise Exception('Model Hash in Subtuple is not the same as in local medias')


def put_opener(subtuple, subtuple_directory):
    from substrapp.models import DataManager

    try:
        datamanager = DataManager.objects.get(pk=subtuple['dataset']['openerHash'])
    except Exception as e:
        raise e

    data_opener_hash = get_hash(datamanager.data_opener.path)
    if data_opener_hash != subtuple['dataset']['openerHash']:
        raise Exception('DataOpener Hash in Subtuple is not the same as in local db')

    opener_dst_path = path.join(subtuple_directory, 'opener/opener.py')
    if not os.path.exists(opener_dst_path):
        os.link(datamanager.data_opener.path, opener_dst_path)


def put_data_sample(subtuple, subtuple_directory):
    from substrapp.models import DataSample

    for data_sample_key in subtuple['dataset']['keys']:
        try:
            data_sample = DataSample.objects.get(pk=data_sample_key)
        except Exception as e:
            raise e
        else:
            data_sample_hash = dirhash(data_sample.path, 'sha256')
            if data_sample_hash != data_sample_key:
                raise Exception('Data Sample Hash in Subtuple is not the same as in local db')

            # create a symlink on the folder containing data
            try:
                subtuple_data_directory = path.join(subtuple_directory, 'data', data_sample_key)
                os.symlink(data_sample.path, subtuple_data_directory)
            except Exception as e:
                logging.error(e, exc_info=True)
                raise Exception('Failed to create sym link for subtuple data sample')


def put_metric(subtuple_directory, objective):
    metrics_dst_path = path.join(subtuple_directory, 'metrics/metrics.py')
    if not os.path.exists(metrics_dst_path):
        os.link(objective.metrics.path, metrics_dst_path)


def put_algo(subtuple_directory, algo_content):
    try:
        uncompress_content(algo_content, subtuple_directory)
    except Exception as e:
        logging.error('Fail to uncompress algo file')
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
    data, st = invokeLedger(fcn=fail_type,
                            args=[f'{key}', f'{err_msg}'],
                            sync=True)

    if st is not status.HTTP_201_CREATED:
        logging.error(data, exc_info=True)

    logging.info('Successfully passed the subtuple to failed')
    return data


# Instatiate Ressource Manager in BaseManager to share it between celery concurrent tasks
BaseManager.register('ResourcesManager', ResourcesManager)
manager = BaseManager()
manager.start()
resources_manager = manager.ResourcesManager()


@app.task(ignore_result=False)
def prepareTrainTuple(subtuple):
    from django_celery_results.models import TaskResult

    fltask = None
    worker_queue = f"{settings.LEDGER['name']}.worker"

    if 'fltask' in subtuple and subtuple['fltask']:
        fltask = subtuple['fltask']
        flresults = TaskResult.objects.filter(task_name='substrapp.tasks.computeTask',
                                              result__icontains=f'"fltask": "{fltask}"')

        if flresults and flresults.count() > 0:
            worker_queue = json.loads(flresults.first().as_dict()['result'])['worker']

    try:
        # Log Start of the Subtuple
        start_type = 'logStartTrain'
        data, st = invokeLedger(fcn=start_type,
                                args=[f'{subtuple["key"]}'],
                                sync=True)

        if st not in (status.HTTP_201_CREATED, status.HTTP_408_REQUEST_TIMEOUT):
            logging.error(
                f'Failed to invoke ledger on prepareTask traintuple. Error: {data}')
        else:
            computeTask.apply_async(('traintuple', subtuple, 'inModels', fltask), queue=worker_queue)

    except Exception as e:
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        return fail(subtuple['key'], error_code, 'traintuple')


@app.task(ignore_result=False)
def prepareTestTuple(subtuple):
    from django_celery_results.models import TaskResult

    fltask = None
    worker_queue = f"{settings.LEDGER['name']}.worker"

    if 'fltask' in subtuple and subtuple['fltask']:
        fltask = subtuple['fltask']
        flresults = TaskResult.objects.filter(task_name='substrapp.tasks.computeTask',
                                              result__icontains=f'"fltask": "{fltask}"')

        if flresults and flresults.count() > 0:
            worker_queue = json.loads(flresults.first().as_dict()['result'])['worker']

    try:
        # Log Start of the Subtuple
        start_type = 'logStartTest'
        data, st = invokeLedger(fcn=start_type,
                                args=[f'{subtuple["key"]}'],
                                sync=True)

        if st not in (status.HTTP_201_CREATED, status.HTTP_408_REQUEST_TIMEOUT):
            logging.error(
                f'Failed to invoke ledger on prepareTask testtuple. Error: {data}')
        else:
            computeTask.apply_async(('testtuple', subtuple, 'model', fltask), queue=worker_queue)

    except Exception as e:
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        return fail(subtuple['key'], error_code, 'testtuple')


def prepareTask(tuple_type, model_type):
    from django_celery_results.models import TaskResult

    try:
        data_owner = get_hash(settings.LEDGER['signcert'])
    except Exception as e:
        logging.error(e, exc_info=True)
    else:

        subtuples, st = queryLedger(fcn="queryFilter",
                                    args=[f'{tuple_type}~worker~status',
                                          f'{data_owner},todo'])

        if st == status.HTTP_200_OK and subtuples is not None:
            for subtuple in subtuples:

                fltask = None
                worker_queue = f"{settings.LEDGER['name']}.worker"

                if 'fltask' in subtuple and subtuple['fltask']:
                    fltask = subtuple['fltask']
                    flresults = TaskResult.objects.filter(
                        task_name='substrapp.tasks.computeTask',
                        result__icontains=f'"fltask": "{fltask}"')

                    if flresults and flresults.count() > 0:
                        worker_queue = json.loads(flresults.first().as_dict()['result'])['worker']

                try:
                    # Log Start of the Subtuple
                    start_type = 'logStartTrain' if tuple_type == 'traintuple' else 'logStartTest' if tuple_type == 'testtuple' else None
                    data, st = invokeLedger(fcn=start_type,
                                            args=[f'{subtuple["key"]}'],
                                            sync=True)

                    if st not in (status.HTTP_201_CREATED, status.HTTP_408_REQUEST_TIMEOUT):
                        logging.error(
                            f'Failed to invoke ledger on prepareTask {tuple_type}. Error: {data}')
                    else:
                        computeTask.apply_async(
                            (tuple_type, subtuple, model_type, fltask),
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
        worker = f"{settings.LEDGER['name']}.worker"
        queue = f"{settings.LEDGER['name']}"

    result = {'worker': worker, 'queue': queue, 'fltask': fltask}

    # Get materials
    try:
        prepareMaterials(subtuple, model_type)
    except Exception as e:
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        fail(subtuple['key'], error_code, tuple_type)
        return result

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
            invoke_fcn = 'logSuccessTrain'
            invoke_args = [f'{subtuple["key"]}',
                           f'{res["end_model_file_hash"]}, {res["end_model_file"]}',
                           f'{res["global_perf"]}',
                           f'Train - {res["job_task_log"]};']

        elif tuple_type == 'testtuple':
            invoke_fcn = 'logSuccessTest'
            invoke_args = [f'{subtuple["key"]}',
                           f'{res["global_perf"]}',
                           f'Test - {res["job_task_log"]};']

        data, st = invokeLedger(fcn=invoke_fcn, args=invoke_args, sync=True)

        if st not in (status.HTTP_201_CREATED, status.HTTP_408_REQUEST_TIMEOUT):
            logging.error('Failed to invoke ledger on logSuccess')
            logging.error(data)

    return result


def prepareMaterials(subtuple, model_type):
    # get subtuple components
    try:
        objective = get_objective(subtuple)
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
        put_data_sample(subtuple, subtuple_directory)
        put_metric(subtuple_directory, objective)
        put_algo(subtuple_directory, algo_content)
        if model_type == 'model':  # testtuple
            put_model(subtuple, subtuple_directory, model_content)
        if model_type == 'inModels':  # traintuple
            put_models(subtuple, subtuple_directory, models_content)

    except Exception as e:
        raise e


def doTask(subtuple, tuple_type):
    subtuple_directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'subtuple', subtuple['key'])
    org_name = getattr(settings, 'ORG_NAME')

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

        ##########################################
        # RESOLVE SYMLINKS
        # TO DO:
        #   - Verify that real paths are safe
        #   - Try to see if it's clean to do that
        ##########################################
        symlinks_volume = {}
        for subfolder in os.listdir(data_path):
            real_path = os.path.realpath(os.path.join(data_path, subfolder))
            symlinks_volume[real_path] = {'bind': f'{real_path}', 'mode': 'ro'}

        ##########################################

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
            algo_command = 'train'    # main command

            # add list of inmodels
            if subtuple['inModels'] is not None:
                inmodels = [subtuple_model["traintupleKey"] for subtuple_model in subtuple['inModels']]
                algo_command = f"{algo_command} {' '.join(inmodels)}"

            # add fltask rank for training
            if flrank is not None:
                algo_command = f"{algo_command} --rank {flrank}"

        elif tuple_type == 'testtuple':
            algo_command = 'predict'    # main command

            inmodels = subtuple['model']["traintupleKey"]
            algo_command = f'{algo_command} {inmodels}'

        # local volume for fltask
        if fltask is not None and tuple_type == 'traintuple':
            flvolume = f'local-{fltask}-{org_name}'
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
                                      volumes={**volumes, **model_volume, **symlinks_volume},
                                      command=algo_command,
                                      remove_image=remove_image)
        # save model in database
        if tuple_type == 'traintuple':
            from substrapp.models import Model
            end_model_path = path.join(subtuple_directory, 'model/model')
            end_model_file_hash = get_hash(end_model_path, subtuple['key'])
            try:
                instance = Model.objects.create(pkhash=end_model_file_hash, validated=True)
            except Exception as e:
                error_code = compute_error_code(e)
                logging.error(error_code, exc_info=True)
                return fail(subtuple['key'], error_code, tuple_type)

            with open(end_model_path, 'rb') as f:
                instance.file.save('model', f)
            current_site = getattr(settings, "DEFAULT_DOMAIN")
            end_model_file = f'{current_site}{reverse("substrapp:model-file", args=[end_model_file_hash])}'

        # compute metric task
        metrics_path = path.join(getattr(settings, 'PROJECT_ROOT'), 'base_metrics')   # base metrics comes with substrabac
        metrics_docker = f'metrics_{tuple_type}'.lower()  # tag must be lowercase for docker
        metrics_docker_name = f'{metrics_docker}_{subtuple["key"]}'
        compute_docker(client=client,
                       resources_manager=resources_manager,
                       dockerfile_path=metrics_path,
                       image_name=metrics_docker,
                       container_name=metrics_docker_name,
                       volumes={**volumes, **symlinks_volume},
                       command=None,
                       remove_image=remove_image)

        # load performance
        with open(path.join(pred_path, 'perf.json'), 'r') as perf_file:
            perf = json.load(perf_file)
        global_perf = perf['all']

    except Exception as e:
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
            flvolume = f'local-{fltask}-{org_name}'
            local_volume = client.volumes.get(volume_id=flvolume)
            try:
                local_volume.remove(force=True)
            except:
                logging.error(f'Cannot remove local volume {flvolume}', exc_info=True)

    return result

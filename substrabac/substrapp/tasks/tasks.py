from __future__ import absolute_import, unicode_literals

import os
import shutil
import tempfile
from os import path

from checksumdir import dirhash
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse

from substrabac.celery import app
from substrapp.ledger_utils import queryLedger, invokeLedger
from substrapp.utils import get_hash, create_directory, get_remote_file, uncompress_content
from substrapp.tasks.utils import ResourcesManager, compute_docker
from substrapp.tasks.exception_handler import compute_error_code

import docker
import json
from multiprocessing.managers import BaseManager

import logging


def get_objective(subtuple):
    from substrapp.models import Objective

    objectiveHash = subtuple['objective']['hash']

    objective = None
    try:
        objective = Objective.objects.get(pk=objectiveHash)
    except ObjectDoesNotExist:
        pass

    # get objective from ledger as it is not available in local db and store it in local db
    if objective is None or not objective.metrics:
        content, computed_hash = get_remote_file(subtuple['objective']['metrics'])

        objective, _ = Objective.objects.update_or_create(pkhash=objectiveHash, validated=True)

        tmp_file = tempfile.TemporaryFile()
        tmp_file.write(content)
        objective.metrics.save('metrics.py', tmp_file)

    return objective


def get_algo(subtuple):
    algo_content, _ = get_remote_file(subtuple['algo'])
    return algo_content


def _get_model(model):
    model_content, _ = get_remote_file(model, model['traintupleKey'])
    return model_content


def get_model(subtuple):
    model = subtuple.get('model')
    if model:
        return _get_model(model)
    else:
        return None


def get_models(subtuple):
    input_models = subtuple.get('inModels')
    if input_models:
        return [_get_model(item) for item in input_models]
    else:
        return []


def _put_model(subtuple, subtuple_directory, model_content, model_hash, traintuple_key):
    if not model_content:
        raise Exception('Model content should not be empty')

    from substrapp.models import Model

    # store a model in local subtuple directory from input model content
    model_dst_path = path.join(subtuple_directory, f'model/{traintuple_key}')
    model = None
    try:
        model = Model.objects.get(pk=model_hash)
    except ObjectDoesNotExist:  # write it to local disk
        with open(model_dst_path, 'wb') as f:
            f.write(model_content)
    else:
        # verify that local db model file is not corrupted
        if get_hash(model.file.path, traintuple_key) != model_hash:
            raise Exception('Model Hash in Subtuple is not the same as in local db')

        if not os.path.exists(model_dst_path):
            os.link(model.file.path, model_dst_path)
        else:
            # verify that local subtuple model file is not corrupted
            if get_hash(model_dst_path, traintuple_key) != model_hash:
                raise Exception('Model Hash in Subtuple is not the same as in local medias')


def put_model(subtuple, subtuple_directory, model_content):
    return _put_model(subtuple, subtuple_directory, model_content, subtuple['model']['hash'],
                      subtuple['model']['traintupleKey'])


def put_models(subtuple, subtuple_directory, models_content):
    if not models_content:
        raise Exception('Models content should not be empty')

    for model_content, model in zip(models_content, subtuple['inModels']):
        _put_model(model, subtuple_directory, model_content, model['hash'], model['traintupleKey'])


def put_opener(subtuple, subtuple_directory):
    from substrapp.models import DataManager
    data_opener_hash = subtuple['dataset']['openerHash']

    datamanager = DataManager.objects.get(pk=data_opener_hash)

    # verify that local db opener file is not corrupted
    if get_hash(datamanager.data_opener.path) != data_opener_hash:
        raise Exception('DataOpener Hash in Subtuple is not the same as in local db')

    opener_dst_path = path.join(subtuple_directory, 'opener/opener.py')
    if not os.path.exists(opener_dst_path):
        os.link(datamanager.data_opener.path, opener_dst_path)
    else:
        # verify that local subtuple data opener file is not corrupted
        if get_hash(opener_dst_path) != data_opener_hash:
            raise Exception('DataOpener Hash in Subtuple is not the same as in local medias')


def put_data_sample(subtuple, subtuple_directory):
    from substrapp.models import DataSample

    for data_sample_key in subtuple['dataset']['keys']:
        data_sample = DataSample.objects.get(pk=data_sample_key)
        data_sample_hash = dirhash(data_sample.path, 'sha256')
        if data_sample_hash != data_sample_key:
            raise Exception('Data Sample Hash in Subtuple is not the same as in local db')

        # create a symlink on the folder containing data
        subtuple_data_directory = path.join(subtuple_directory, 'data', data_sample_key)
        try:
            os.symlink(data_sample.path, subtuple_data_directory)
        except OSError as e:
            logging.exception(e)
            raise Exception('Failed to create sym link for subtuple data sample')


def put_metric(subtuple_directory, objective):
    metrics_dst_path = path.join(subtuple_directory, 'metrics/metrics.py')
    if not os.path.exists(metrics_dst_path):
        os.link(objective.metrics.path, metrics_dst_path)


def put_algo(subtuple_directory, algo_content):
    uncompress_content(algo_content, subtuple_directory)


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
        logging.exception(e)


def log_fail_subtuple(key, err_msg, tuple_type):
    err_msg = str(err_msg).replace('"', "'").replace('\\', "").replace('\\n', "")[:200]
    fail_type = 'logFailTrain' if tuple_type == 'traintuple' else 'logFailTest'
    data, st = invokeLedger(fcn=fail_type,
                            args=[f'{key}', f'{err_msg}'],
                            sync=True)

    if st != status.HTTP_201_CREATED:
        logging.error(data, exc_info=True)
    else:
        logging.info('Successfully passed the subtuple to failed')
    return data


# Instatiate Ressource Manager in BaseManager to share it between celery concurrent tasks
BaseManager.register('ResourcesManager', ResourcesManager)
manager = BaseManager()
manager.start()
resources_manager = manager.ResourcesManager()


@app.task(ignore_result=False)
def prepareTuple(subtuple, tuple_type, model_type):
    from django_celery_results.models import TaskResult

    fltask = None
    worker_queue = f"{settings.LEDGER['name']}.worker"

    if 'fltask' in subtuple and subtuple['fltask']:
        fltask = subtuple['fltask']
        flresults = TaskResult.objects.filter(
            task_name='substrapp.tasks.tasks.computeTask',
            result__icontains=f'"fltask": "{fltask}"')

        if flresults and flresults.count() > 0:
            worker_queue = json.loads(flresults.first().as_dict()['result'])['worker']

    try:
        # Log Start of the Subtuple

        start_type = None
        if tuple_type == 'traintuple':
            start_type = 'logStartTrain'
        elif tuple_type == 'testtuple':
            start_type = 'logStartTest'

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
        return log_fail_subtuple(subtuple['key'], error_code, tuple_type)


def prepareTask(tuple_type, model_type):
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
                prepareTuple(subtuple, tuple_type, model_type)


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
    except Exception:
        worker = f"{settings.LEDGER['name']}.worker"
        queue = f"{settings.LEDGER['name']}"

    result = {'worker': worker, 'queue': queue, 'fltask': fltask}

    # Get materials
    try:
        prepareMaterials(subtuple, model_type)
    except Exception as e:
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        log_fail_subtuple(subtuple['key'], error_code, tuple_type)
        return result

    logging.info(f'Prepare Task success {tuple_type}')

    try:
        res = doTask(subtuple, tuple_type)
    except Exception as e:
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        log_fail_subtuple(subtuple['key'], error_code, tuple_type)
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
    objective = get_objective(subtuple)
    algo_content = get_algo(subtuple)
    if model_type == 'model':
        model_content = get_model(subtuple)
    elif model_type == 'inModels':
        models_content = get_models(subtuple)

    # create subtuple
    subtuple_directory = build_subtuple_folders(subtuple)  # do not put anything in pred folder
    put_opener(subtuple, subtuple_directory)
    put_data_sample(subtuple, subtuple_directory)
    put_metric(subtuple_directory, objective)
    put_algo(subtuple_directory, algo_content)
    if model_type == 'model':  # testtuple
        put_model(subtuple, subtuple_directory, model_content)
    elif model_type == 'inModels' and models_content:  # traintuple
        put_models(subtuple, subtuple_directory, models_content)


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
                return log_fail_subtuple(subtuple['key'], error_code, tuple_type)

            with open(end_model_path, 'rb') as f:
                instance.file.save('model', f)
            current_site = getattr(settings, "DEFAULT_DOMAIN")
            end_model_file = f'{current_site}{reverse("substrapp:model-file", args=[end_model_file_hash])}'

        # compute metric task
        metrics_path = path.join(getattr(settings, 'PROJECT_ROOT'), 'containers/metrics')   # comes with substrabac
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
            except Exception:
                logging.error(f'Cannot remove local volume {flvolume}', exc_info=True)

    return result

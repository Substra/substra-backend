from __future__ import absolute_import, unicode_literals

import os
import shutil
import tempfile
from os import path
import json
from multiprocessing.managers import BaseManager
import logging

import docker
from checksumdir import dirhash
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rest_framework.reverse import reverse
from celery.result import AsyncResult
from celery.exceptions import Ignore

from backend.celery import app
from substrapp.utils import get_hash, get_owner, create_directory, uncompress_content
from substrapp.ledger_utils import (log_start_tuple, log_success_tuple, log_fail_tuple,
                                    query_tuples, LedgerError, LedgerStatusError, get_object_from_ledger)
from substrapp.tasks.utils import ResourcesManager, compute_docker, get_asset_content, list_files
from substrapp.tasks.exception_handler import compute_error_code


def get_objective(subtuple):
    from substrapp.models import Objective

    objective_hash = subtuple['objective']['hash']

    try:
        objective = Objective.objects.get(pk=objective_hash)
    except ObjectDoesNotExist:
        objective = None

    # get objective from ledger as it is not available in local db and store it in local db
    if objective is None or not objective.metrics:
        objective_metadata = get_object_from_ledger(objective_hash, 'queryObjective')

        content = get_asset_content(
            objective_metadata['metrics']['storageAddress'],
            objective_metadata['owner'],
            objective_metadata['metrics']['hash'],
        )

        objective, _ = Objective.objects.update_or_create(pkhash=objective_hash, validated=True)

        tmp_file = tempfile.TemporaryFile()
        tmp_file.write(content)
        objective.metrics.save('metrics.archive', tmp_file)

    return objective.metrics.read()


def get_algo(subtuple):
    algo_hash = subtuple['algo']['hash']
    algo_metadata = get_object_from_ledger(algo_hash, 'queryAlgo')

    algo_content = get_asset_content(
        algo_metadata['content']['storageAddress'],
        algo_metadata['owner'],
        algo_metadata['content']['hash'],
    )

    return algo_content


def _get_model(model):
    traintuple_hash = model['traintupleKey']
    traintuple_metadata = get_object_from_ledger(traintuple_hash, 'queryTraintuple')

    model_content = get_asset_content(
        traintuple_metadata['outModel']['storageAddress'],
        traintuple_metadata['dataset']['worker'],
        traintuple_metadata['outModel']['hash'],
        salt=traintuple_hash,
    )

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


def put_metric(subtuple_directory, metrics_content):
    metrics_dst_path = path.join(subtuple_directory, 'metrics/')
    uncompress_content(metrics_content, metrics_dst_path)


def put_algo(subtuple_directory, algo_content):
    uncompress_content(algo_content, subtuple_directory)


def build_subtuple_folders(subtuple):
    # create a folder named `subtuple['key']` in /medias/subtuple/ with 5 subfolders opener, data, model, pred, metrics
    subtuple_directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'subtuple', subtuple['key'])
    create_directory(subtuple_directory)

    for folder in ['opener', 'data', 'model', 'pred', 'metrics']:
        create_directory(path.join(subtuple_directory, folder))

    return subtuple_directory


def remove_subtuple_materials(subtuple_directory):
    logging.info('Remove subtuple materials')
    list_files(subtuple_directory)
    try:
        shutil.rmtree(subtuple_directory)
    except Exception as e:
        logging.exception(e)
    finally:
        list_files(subtuple_directory)


# Instatiate Ressource Manager in BaseManager to share it between celery concurrent tasks
BaseManager.register('ResourcesManager', ResourcesManager)
manager = BaseManager()
manager.start()
resources_manager = manager.ResourcesManager()


@app.task(ignore_result=True)
def prepare_training_task():
    prepare_task('traintuple')


@app.task(ignore_result=True)
def prepare_testing_task():
    prepare_task('testtuple')


def prepare_task(tuple_type):
    data_owner = get_owner()
    worker_queue = f"{settings.LEDGER['name']}.worker"
    tuples = query_tuples(tuple_type, data_owner)

    for subtuple in tuples:
        tkey = subtuple['key']
        # Verify that tuple task does not already exist
        if AsyncResult(tkey).state == 'PENDING':
            prepare_tuple.apply_async(
                (subtuple, tuple_type),
                task_id=tkey,
                queue=worker_queue
            )
        else:
            print(f'[Scheduler] Tuple task ({tkey}) already exists')


@app.task(ignore_result=False)
def prepare_tuple(subtuple, tuple_type):
    from django_celery_results.models import TaskResult

    compute_plan_id = None
    worker_queue = f"{settings.LEDGER['name']}.worker"

    if 'computePlanID' in subtuple and subtuple['computePlanID']:
        compute_plan_id = subtuple['computePlanID']
        flresults = TaskResult.objects.filter(
            task_name='substrapp.tasks.tasks.compute_task',
            result__icontains=f'"computePlanID": "{compute_plan_id}"')

        if flresults and flresults.count() > 0:
            worker_queue = json.loads(flresults.first().as_dict()['result'])['worker']

    try:
        log_start_tuple(tuple_type, subtuple['key'])
    except LedgerStatusError as e:
        # Do not log_fail_tuple in this case, because prepare_tuple task are not unique
        # in case of multiple instances of substra backend running for the same organisation
        # So prepare_tuple tasks are ignored if it cannot log_start_tuple
        logging.exception(e)
        raise Ignore()

    try:
        compute_task.apply_async(
            (tuple_type, subtuple, compute_plan_id),
            queue=worker_queue)
    except Exception as e:
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)
        log_fail_tuple(tuple_type, subtuple['key'], error_code)


@app.task(bind=True, ignore_result=False)
def compute_task(self, tuple_type, subtuple, compute_plan_id):

    try:
        worker = self.request.hostname.split('@')[1]
        queue = self.request.delivery_info['routing_key']
    except Exception:
        worker = f"{settings.LEDGER['name']}.worker"
        queue = f"{settings.LEDGER['name']}"

    result = {'worker': worker, 'queue': queue, 'computePlanID': compute_plan_id}

    try:
        prepare_materials(subtuple, tuple_type)
        res = do_task(subtuple, tuple_type)
    except Exception as e:
        error_code = compute_error_code(e)
        logging.error(error_code, exc_info=True)

        try:
            log_fail_tuple(tuple_type, subtuple['key'], error_code)
        except LedgerError as e:
            logging.exception(e)

        return result

    try:
        log_success_tuple(tuple_type, subtuple['key'], res)
    except LedgerError as e:
        logging.exception(e)

    return result


def prepare_materials(subtuple, tuple_type):

    logging.info(f'Prepare materials for {tuple_type} task')

    # get subtuple components
    metrics_content = get_objective(subtuple)
    algo_content = get_algo(subtuple)
    if tuple_type == 'testtuple':
        model_content = get_model(subtuple)
    elif tuple_type == 'traintuple':
        models_content = get_models(subtuple)
    else:
        raise NotImplementedError()

    # create subtuple
    subtuple_directory = build_subtuple_folders(subtuple)
    put_algo(subtuple_directory, algo_content)
    put_opener(subtuple, subtuple_directory)
    put_metric(subtuple_directory, metrics_content)
    put_data_sample(subtuple, subtuple_directory)
    if tuple_type == 'testtuple':
        put_model(subtuple, subtuple_directory, model_content)
    elif tuple_type == 'traintuple' and models_content:
        put_models(subtuple, subtuple_directory, models_content)

    logging.info(f'Prepare materials for {tuple_type} task: success')
    list_files(subtuple_directory)


def do_task(subtuple, tuple_type):
    subtuple_directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'subtuple', subtuple['key'])
    org_name = getattr(settings, 'ORG_NAME')

    # compute plan / federated learning variables
    compute_plan_id = None
    rank = None

    if 'computePlanID' in subtuple and subtuple['computePlanID']:
        compute_plan_id = subtuple['computePlanID']
        rank = int(subtuple['rank'])

    client = docker.from_env()

    try:
        result = _do_task(
            client,
            subtuple_directory,
            tuple_type,
            subtuple,
            compute_plan_id,
            rank,
            org_name
        )
    except Exception as e:
        if compute_plan_id is not None:
            rank = -1  # -1 means last subtuple in the compute plan
        raise e
    finally:
        # Clean subtuple materials
        if settings.TASK['CLEAN_EXECUTION_ENVIRONMENT']:
            remove_subtuple_materials(subtuple_directory)
            if rank == -1:
                volume_id = f'local-{compute_plan_id}-{org_name}'
                local_volume = client.volumes.get(volume_id=volume_id)
                try:
                    local_volume.remove(force=True)
                except Exception:
                    logging.error(f'Cannot remove local volume {volume_id}', exc_info=True)

    return result


def _do_task(client, subtuple_directory, tuple_type, subtuple, compute_plan_id, rank, org_name):

    model_path = path.join(subtuple_directory, 'model')
    data_path = path.join(subtuple_directory, 'data')
    pred_path = path.join(subtuple_directory, 'pred')
    opener_file = path.join(subtuple_directory, 'opener/opener.py')
    algo_path = path.join(subtuple_directory)

    algo_docker = f'substra/algo_{subtuple["key"][0:8]}'.lower()  # tag must be lowercase for docker
    algo_docker_name = f'{tuple_type}_{subtuple["key"][0:8]}'

    remove_image = not((compute_plan_id is not None and rank != -1) or settings.TASK['CACHE_DOCKER_IMAGES'])

    # VOLUMES

    symlinks_volume = {}
    for subfolder in os.listdir(data_path):
        real_path = os.path.realpath(os.path.join(data_path, subfolder))
        symlinks_volume[real_path] = {'bind': f'{real_path}', 'mode': 'ro'}

    volumes = {
        data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
        pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
        opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}
    }

    model_volume = {
        model_path: {'bind': '/sandbox/model', 'mode': 'rw'}
    }

    # local volume for training subtuple in compute plan
    if compute_plan_id is not None and tuple_type == 'traintuple':
        volume_id = f'local-{compute_plan_id}-{org_name}'
        if rank == 0:
            client.volumes.create(name=volume_id)
        else:
            client.volumes.get(volume_id=volume_id)
        model_volume[volume_id] = {'bind': '/sandbox/local', 'mode': 'rw'}

    # generate command
    if tuple_type == 'traintuple':
        command = 'train'
        algo_docker_name = f'{algo_docker_name}_{command}'

        if subtuple['inModels'] is not None:
            inmodels = [subtuple_model["traintupleKey"] for subtuple_model in subtuple['inModels']]
            command = f"{command} {' '.join(inmodels)}"

        if rank is not None:
            command = f"{command} --rank {rank}"

    elif tuple_type == 'testtuple':
        command = 'predict'
        algo_docker_name = f'{algo_docker_name}_{command}'
        inmodels = subtuple['model']["traintupleKey"]
        command = f'{command} {inmodels}'

    compute_docker(
        client=client,
        resources_manager=resources_manager,
        dockerfile_path=algo_path,
        image_name=algo_docker,
        container_name=algo_docker_name,
        volumes={**volumes, **model_volume, **symlinks_volume},
        command=command,
        remove_image=remove_image,
        remove_container=settings.TASK['CLEAN_EXECUTION_ENVIRONMENT'],
        capture_logs=settings.TASK['CAPTURE_LOGS']
    )

    # save model in database
    if tuple_type == 'traintuple':
        end_model_file, end_model_file_hash = save_model(subtuple_directory, subtuple['key'])

    # evaluation
    metrics_path = f'{subtuple_directory}/metrics'
    eval_docker = f'substra/metrics_{subtuple["key"][0:8]}'.lower()  # tag must be lowercase for docker
    eval_docker_name = f'{tuple_type}_{subtuple["key"][0:8]}_eval'

    compute_docker(
        client=client,
        resources_manager=resources_manager,
        dockerfile_path=metrics_path,
        image_name=eval_docker,
        container_name=eval_docker_name,
        volumes={**volumes, **symlinks_volume},
        command=None,
        remove_image=remove_image,
        remove_container=settings.TASK['CLEAN_EXECUTION_ENVIRONMENT'],
        capture_logs=settings.TASK['CAPTURE_LOGS']
    )

    # load performance
    with open(path.join(pred_path, 'perf.json'), 'r') as perf_file:
        perf = json.load(perf_file)
    global_perf = perf['all']

    result = {'global_perf': global_perf}

    if tuple_type == 'traintuple':
        result['end_model_file_hash'] = end_model_file_hash
        result['end_model_file'] = end_model_file

    return result


def save_model(subtuple_directory, subtuple_key):
    from substrapp.models import Model
    end_model_path = path.join(subtuple_directory, 'model/model')
    end_model_file_hash = get_hash(end_model_path, subtuple_key)
    instance = Model.objects.create(pkhash=end_model_file_hash, validated=True)

    with open(end_model_path, 'rb') as f:
        instance.file.save('model', f)
    current_site = getattr(settings, "DEFAULT_DOMAIN")
    end_model_file = f'{current_site}{reverse("substrapp:model-file", args=[end_model_file_hash])}'

    return end_model_file, end_model_file_hash

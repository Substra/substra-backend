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
from celery.task import Task

from backend.celery import app
from substrapp.utils import get_hash, get_owner, create_directory, uncompress_content
from substrapp.ledger_utils import (log_start_tuple, log_success_tuple, log_fail_tuple,
                                    query_tuples, LedgerError, LedgerStatusError, get_object_from_ledger)
from substrapp.tasks.utils import ResourcesManager, compute_docker, get_asset_content, list_files
from substrapp.tasks.exception_handler import compute_error_code


PREFIX_HEAD_FILENAME = 'head_'
PREFIX_TRUNK_FILENAME = 'trunk_'

TRAINTUPLE_TYPE = 'traintuple'
AGGREGATETUPLE_TYPE = 'aggregatetuple'
COMPOSITE_TRAINTUPLE_TYPE = 'compositeTraintuple'
TESTTUPLE_TYPE = 'testtuple'


class TasksError(Exception):
    pass


def get_objective(tuple_):
    from substrapp.models import Objective

    objective_hash = tuple_['objective']['hash']

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


def prepare_objective(directory, tuple_):
    """Prepare objective for tuple execution."""
    metrics_content = get_objective(tuple_)
    dst_path = path.join(directory, 'metrics/')
    uncompress_content(metrics_content, dst_path)


def get_algo(tuple_type, tuple_):
    """Get algo from ledger."""
    query_method_names_mapper = {
        TRAINTUPLE_TYPE: 'queryAlgo',
        COMPOSITE_TRAINTUPLE_TYPE: 'queryCompositeAlgo',
        AGGREGATETUPLE_TYPE: 'queryAggregateAlgo',
    }

    if tuple_type not in query_method_names_mapper:
        raise TasksError(f'Cannot find algo from tuple type {tuple_type}: {tuple_}')
    method_name = query_method_names_mapper[tuple_type]

    key = tuple_['algo']['hash']
    metadata = get_object_from_ledger(key, method_name)

    content = get_asset_content(
        metadata['content']['storageAddress'],
        metadata['owner'],
        metadata['content']['hash'],
    )
    return content


def prepare_algo(directory, tuple_type, tuple_):
    """Prepare algo for tuple execution."""
    content = get_algo(tuple_type, tuple_)
    uncompress_content(content, directory)


def tuple_get_owner(tuple_type, tuple_):
    """Get node owner from tuple metadata.

    Applies to traintuple, composite traintuple and aggregatetuple.
    """
    if tuple_type == AGGREGATETUPLE_TYPE:
        return tuple_['worker']
    return tuple_['dataset']['worker']


def find_training_step_tuple_from_key(tuple_key):
    """Get tuple type and tuple metadata from tuple key.

    Applies to traintuple, composite traintuple and aggregatetuple.
    """
    metadata = get_object_from_ledger(tuple_key, 'queryModelDetails')
    if metadata.get('aggregatetuple'):
        return AGGREGATETUPLE_TYPE, metadata['aggregatetuple']
    if metadata.get('compositeTraintuple'):
        return COMPOSITE_TRAINTUPLE_TYPE, metadata['compositeTraintuple']
    if metadata.get('traintuple'):
        return TRAINTUPLE_TYPE, metadata['traintuple']
    raise TasksError(
        f'Key {tuple_key}: no tuple found for training step: model: {metadata}')


def get_model_content(tuple_type, tuple_key, tuple_, out_model):
    """Get out model content."""
    owner = tuple_get_owner(tuple_type, tuple_)
    return get_asset_content(
        out_model['storageAddress'],
        owner,
        out_model['hash'],
        salt=tuple_key,
    )


def prepare_traintuple_input_models(directory, tuple_):
    """Get traintuple input models content."""
    input_models = tuple_.get('inModels')
    if not input_models:
        return

    model_keys = [m['traintupleKey'] for m in input_models]
    model_contents = []
    for key in model_keys:
        tuple_type, metadata = find_training_step_tuple_from_key(key)
        if tuple_type not in (AGGREGATETUPLE_TYPE, TRAINTUPLE_TYPE):
            raise TasksError(f'Traintuple: invalid input model: type={tuple_type}')
        model = get_model_content(tuple_type, key, metadata, metadata['outModel'])
        model_contents.append(model)

    for content, model in zip(model_contents, tuple_['inModels']):
        _put_model(directory, content, model['hash'], model['traintupleKey'])


def prepare_aggregatetuple_input_models(directory, tuple_):
    """Get aggregatetuple input models content."""
    input_models = tuple_.get('inModels')
    if not input_models:
        return

    model_contents = []
    model_keys = [m['traintupleKey'] for m in input_models]
    for key in model_keys:
        tuple_type, metadata = find_training_step_tuple_from_key(key)

        if tuple_type in (TRAINTUPLE_TYPE, AGGREGATETUPLE_TYPE):
            model = get_model_content(tuple_type, key, metadata, metadata['outModel'])

        elif tuple_type == COMPOSITE_TRAINTUPLE_TYPE:  # get output trunk model
            model = get_model_content(
                tuple_type, key, metadata, metadata['outTrunkModel']['outModel'],
            )

        else:
            raise TasksError(f'Aggregatuple: invalid input model: type={tuple_type}')

        model_contents.append(model)

    for content, model in zip(model_contents, tuple_['inModels']):
        _put_model(directory, content, model['hash'], model['traintupleKey'])


def prepare_composite_traintuple_input_models(directory, tuple_):
    """Get composite traintuple input models content."""
    head_model = tuple_.get('inHeadModel')
    trunk_model = tuple_.get('inTrunkModel')
    if not head_model or not trunk_model:  # head and trunk models are optional
        return []

    # get head model
    head_model_key = head_model['traintupleKey']
    tuple_type, metadata = find_training_step_tuple_from_key(head_model_key)
    # head model must refer to a composite traintuple
    if tuple_type != COMPOSITE_TRAINTUPLE_TYPE:
        raise TasksError(f'CompositeTraintuple: invalid head input model: type={tuple_type}')
    # get the output head model
    head_model_content = get_model_content(
        tuple_type, head_model_key, metadata, metadata['outHeadModel']['outModel'],
    )

    # get trunk model
    trunk_model_key = trunk_model['traintupleKey']
    tuple_type, metadata = find_training_step_tuple_from_key(trunk_model_key)
    # trunk model must refer to a composite traintuple or an aggregatetuple
    if tuple_type == COMPOSITE_TRAINTUPLE_TYPE:  # get output trunk model
        trunk_model_content = get_model_content(
            tuple_type, trunk_model_key, metadata, metadata['outTrunkModel']['outModel'],
        )
    elif tuple_type == AGGREGATETUPLE_TYPE:
        trunk_model_content = get_model_content(
            tuple_type, trunk_model_key, metadata, metadata['outModel'],
        )
    else:
        raise TasksError(f'CompositeTraintuple: invalid trunk input model: type={tuple_type}')

    # put head and trunk models
    _put_model(directory, head_model_content,
               tuple_['inHeadModel']['hash'],
               tuple_['inHeadModel']['traintupleKey'],
               filename_prefix=PREFIX_HEAD_FILENAME)
    _put_model(directory, trunk_model_content,
               tuple_['inTrunkModel']['hash'],
               tuple_['inTrunkModel']['traintupleKey'],
               filename_prefix=PREFIX_TRUNK_FILENAME)


def prepare_testtuple_input_models(directory, tuple_):
    """Get testtuple input models content."""
    traintuple_type = tuple_['traintupleType']
    traintuple_key = tuple_['traintupleKey']

    # TODO we should use the find method to be consistent with the traintuple

    if traintuple_type == TRAINTUPLE_TYPE:
        metadata = get_object_from_ledger(traintuple_key, 'queryTraintuple')
        model = get_model_content(traintuple_type, traintuple_key, metadata, metadata['outModel'])
        model_hash = metadata['outModel']['hash']
        _put_model(directory, model, model_hash, traintuple_key)

    elif traintuple_type == COMPOSITE_TRAINTUPLE_TYPE:
        metadata = get_object_from_ledger(traintuple_key, 'queryCompositeTraintuple')
        head_content = get_model_content(
            traintuple_type, traintuple_key, metadata, metadata['outHeadModel']['outModel'],
        )
        trunk_content = get_model_content(
            traintuple_type, traintuple_key, metadata, metadata['outTrunkModel']['outModel'],
        )
        _put_model(directory, head_content, metadata['outHeadModel']['outModel']['hash'],
                   traintuple_key, filename_prefix=PREFIX_HEAD_FILENAME)
        _put_model(directory, trunk_content, metadata['outTrunkModel']['outModel']['hash'],
                   traintuple_key, filename_prefix=PREFIX_TRUNK_FILENAME)

    else:
        raise TasksError(f"Testtuple from type '{traintuple_type}' not supported")


def _put_model(subtuple_directory, model_content, model_hash, traintuple_hash, filename_prefix=''):
    if not model_content:
        raise Exception('Model content should not be empty')

    from substrapp.models import Model

    # store a model in local subtuple directory from input model content
    model_dst_path = path.join(subtuple_directory, f'model/{filename_prefix}{traintuple_hash}')
    model = None
    try:
        model = Model.objects.get(pk=model_hash)
    except ObjectDoesNotExist:  # write it to local disk
        with open(model_dst_path, 'wb') as f:
            f.write(model_content)
    else:
        # verify that local db model file is not corrupted
        if get_hash(model.file.path, traintuple_hash) != model_hash:
            raise Exception('Model Hash in Subtuple is not the same as in local db')

        if not os.path.exists(model_dst_path):
            os.link(model.file.path, model_dst_path)
        else:
            # verify that local subtuple model file is not corrupted
            if get_hash(model_dst_path, traintuple_hash) != model_hash:
                raise Exception('Model Hash in Subtuple is not the same as in local medias')


def prepare_models(directory, tuple_type, tuple_):
    """Prepare models for tuple execution.

    Checks that all input models are compatible with the current tuple to execute.
    """
    if tuple_type == TESTTUPLE_TYPE:
        prepare_testtuple_input_models(directory, tuple_)

    elif tuple_type == TRAINTUPLE_TYPE:
        prepare_traintuple_input_models(directory, tuple_)

    elif tuple_type == COMPOSITE_TRAINTUPLE_TYPE:
        prepare_composite_traintuple_input_models(directory, tuple_)

    elif tuple_type == AGGREGATETUPLE_TYPE:
        prepare_aggregatetuple_input_models(directory, tuple_)

    else:
        raise TasksError(f"task of type : {tuple_type} not implemented")


def prepare_opener(directory, tuple_):
    """Prepare opener for tuple execution."""
    from substrapp.models import DataManager
    data_opener_hash = tuple_['dataset']['openerHash']

    datamanager = DataManager.objects.get(pk=data_opener_hash)

    # verify that local db opener file is not corrupted
    if get_hash(datamanager.data_opener.path) != data_opener_hash:
        raise Exception('DataOpener Hash in Subtuple is not the same as in local db')

    opener_dst_path = path.join(directory, 'opener/opener.py')
    if not os.path.exists(opener_dst_path):
        os.link(datamanager.data_opener.path, opener_dst_path)
    else:
        # verify that local subtuple data opener file is not corrupted
        if get_hash(opener_dst_path) != data_opener_hash:
            raise Exception('DataOpener Hash in Subtuple is not the same as in local medias')


def prepare_data_sample(directory, tuple_):
    """Prepare data samples for tuple execution."""
    from substrapp.models import DataSample
    for data_sample_key in tuple_['dataset']['keys']:
        data_sample = DataSample.objects.get(pk=data_sample_key)
        data_sample_hash = dirhash(data_sample.path, 'sha256')
        if data_sample_hash != data_sample_key:
            raise Exception('Data Sample Hash in tuple is not the same as in local db')

        # create a symlink on the folder containing data
        data_directory = path.join(directory, 'data', data_sample_key)
        try:
            os.symlink(data_sample.path, data_directory)
        except OSError as e:
            logging.exception(e)
            raise Exception('Failed to create sym link for tuple data sample')


def build_subtuple_folders(subtuple):
    # create a folder named `subtuple['key']` in /medias/subtuple/ with 5 subfolders opener, data, model, pred, metrics
    subtuple_directory = get_subtuple_directory(subtuple)
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


def try_remove_local_folder(subtuple, compute_plan_id):
    if settings.TASK['CLEAN_EXECUTION_ENVIRONMENT']:
        if compute_plan_id is not None:
            rank = int(subtuple['rank'])
            if rank == -1:
                remove_local_folder(compute_plan_id)


def remove_local_folder(compute_plan_id):
    client = docker.from_env()
    volume_id = get_volume_id(compute_plan_id)
    try:
        local_volume = client.volumes.get(volume_id=volume_id)
        local_volume.remove(force=True)
    except docker.errors.NotFound:
        pass
    except Exception:
        logging.error(f'Cannot remove local volume {volume_id}', exc_info=True)


# Instatiate Ressource Manager in BaseManager to share it between celery concurrent tasks
BaseManager.register('ResourcesManager', ResourcesManager)
manager = BaseManager()
manager.start()
resources_manager = manager.ResourcesManager()


@app.task(ignore_result=True)
def prepare_training_task():
    prepare_task(TRAINTUPLE_TYPE)


@app.task(ignore_result=True)
def prepare_testing_task():
    prepare_task(TESTTUPLE_TYPE)


@app.task(ignore_result=True)
def prepare_aggregate_task():
    prepare_task(AGGREGATETUPLE_TYPE)


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


class ComputeTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        tuple_type, subtuple, compute_plan_id = self.split_args(args)

        try:
            log_success_tuple(tuple_type, subtuple['key'], retval['result'])
        except LedgerError as e:
            logging.exception(e)

        try:
            try_remove_local_folder(subtuple, compute_plan_id)
        except Exception as e:
            logging.exception(e)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        tuple_type, subtuple, compute_plan_id = self.split_args(args)

        try:
            error_code = compute_error_code(exc)
            logging.error(error_code, exc_info=True)
            log_fail_tuple(tuple_type, subtuple['key'], error_code)
        except LedgerError as e:
            logging.exception(e)

        try:
            try_remove_local_folder(subtuple, compute_plan_id)
        except Exception as e:
            logging.exception(e)

    def split_args(self, celery_args):
        tuple_type = celery_args[0]
        subtuple = celery_args[1]
        compute_plan_id = celery_args[2]
        return tuple_type, subtuple, compute_plan_id


@app.task(bind=True, ignore_result=False, base=ComputeTask)
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
        result['result'] = res
    except Exception as e:
        raise self.retry(
            exc=e,
            countdown=int(getattr(settings, 'CELERY_TASK_RETRY_DELAY_SECONDS')),
            max_retries=int(getattr(settings, 'CELERY_TASK_MAX_RETRIES')))
    finally:
        if settings.TASK['CLEAN_EXECUTION_ENVIRONMENT']:
            try:
                subtuple_directory = get_subtuple_directory(subtuple)
                remove_subtuple_materials(subtuple_directory)
            except Exception as e:
                logging.exception(e)

    return result


def prepare_materials(subtuple, tuple_type):
    logging.info(f'Prepare materials for {tuple_type} task')

    # create directory
    directory = build_subtuple_folders(subtuple)

    # metrics
    if tuple_type == TESTTUPLE_TYPE:
        prepare_objective(directory, subtuple)

    # algo
    traintuple_type = (subtuple['traintupleType'] if tuple_type == TESTTUPLE_TYPE else
                       tuple_type)
    prepare_algo(directory, traintuple_type, subtuple)

    # opener
    if tuple_type in (TESTTUPLE_TYPE, TRAINTUPLE_TYPE, COMPOSITE_TRAINTUPLE_TYPE):
        prepare_opener(directory, subtuple)
        prepare_data_sample(directory, subtuple)

    # input models
    prepare_models(directory, tuple_type, subtuple)

    logging.info(f'Prepare materials for {tuple_type} task: success')
    list_files(directory)


def do_task(subtuple, tuple_type):
    subtuple_directory = get_subtuple_directory(subtuple)
    org_name = getattr(settings, 'ORG_NAME')

    # compute plan / federated learning variables
    compute_plan_id = None
    rank = None

    if 'computePlanID' in subtuple and subtuple['computePlanID']:
        compute_plan_id = subtuple['computePlanID']
        rank = int(subtuple['rank'])

    client = docker.from_env()

    return _do_task(
        client,
        subtuple_directory,
        tuple_type,
        subtuple,
        compute_plan_id,
        rank,
        org_name
    )


def _do_task(client, subtuple_directory, tuple_type, subtuple, compute_plan_id, rank, org_name):

    model_folder = '/sandbox/model'
    model_path = path.join(subtuple_directory, 'model')
    data_path = path.join(subtuple_directory, 'data')
    pred_path = path.join(subtuple_directory, 'pred')
    opener_file = path.join(subtuple_directory, 'opener/opener.py')
    algo_path = path.join(subtuple_directory)
    algo_docker = f'substra/algo_{subtuple["key"][0:8]}'.lower()  # tag must be lowercase for docker
    algo_docker_name = f'{tuple_type}_{subtuple["key"][0:8]}'
    output_head_model_filename = 'head_model'
    output_trunk_model_filename = 'trunk_model'

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
        model_path: {'bind': model_folder, 'mode': 'rw'}
    }

    # local volume for train like tuples in compute plan
    if compute_plan_id is not None and tuple_type != TESTTUPLE_TYPE:
        volume_id = get_volume_id(compute_plan_id)
        try:
            client.volumes.get(volume_id=volume_id)
        except docker.errors.NotFound:
            client.volumes.create(name=volume_id)
        model_volume[volume_id] = {'bind': '/sandbox/local', 'mode': 'rw'}

    # generate command
    if tuple_type == TRAINTUPLE_TYPE:
        command = 'train'
        algo_docker_name = f'{algo_docker_name}_{command}'

        if subtuple['inModels'] is not None:
            in_traintuple_keys = [subtuple_model["traintupleKey"] for subtuple_model in subtuple['inModels']]
            command = f"{command} {' '.join(in_traintuple_keys)}"

        if rank is not None:
            command = f"{command} --rank {rank}"

    elif tuple_type == TESTTUPLE_TYPE:
        command = 'predict'
        algo_docker_name = f'{algo_docker_name}_{command}'

        if COMPOSITE_TRAINTUPLE_TYPE == subtuple['traintupleType']:
            composite_traintuple_key = subtuple['traintupleKey']
            command = f"{command} --input-models-path {model_folder}"
            command = f"{command} --input-head-model-filename {PREFIX_HEAD_FILENAME}{composite_traintuple_key}"
            command = f"{command} --input-trunk-model-filename {PREFIX_TRUNK_FILENAME}{composite_traintuple_key}"
        else:
            in_model = subtuple["traintupleKey"]
            command = f'{command} {in_model}'

    elif tuple_type == COMPOSITE_TRAINTUPLE_TYPE:
        command = 'train'
        algo_docker_name = f'{algo_docker_name}_{command}'

        command = f"{command} --output-models-path {model_folder}"
        command = f"{command} --output-head-model-filename {output_head_model_filename}"
        command = f"{command} --output-trunk-model-filename {output_trunk_model_filename}"

        if subtuple['inHeadModel'] and subtuple['inTrunkModel']:
            command = f"{command} --input-models-path {model_folder}"

            in_head_model = subtuple['inHeadModel']
            in_head_model_key = in_head_model.get('traintupleKey')
            command = f"{command} --input-head-model-filename {PREFIX_HEAD_FILENAME}{in_head_model_key}"

            in_trunk_model = subtuple['inTrunkModel']
            in_trunk_model_key = in_trunk_model.get('traintupleKey')
            command = f"{command} --input-trunk-model-filename {PREFIX_TRUNK_FILENAME}{in_trunk_model_key}"

        if rank is not None:
            command = f"{command} --rank {rank}"

    elif tuple_type == AGGREGATETUPLE_TYPE:
        command = 'aggregate'
        algo_docker_name = f'{algo_docker_name}_{command}'

        if subtuple['inModels'] is not None:
            in_aggregatetuple_keys = [subtuple_model["traintupleKey"] for subtuple_model in subtuple['inModels']]
            command = f"{command} {' '.join(in_aggregatetuple_keys)}"

        if rank is not None:
            command = f"{command} --rank {rank}"

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
    if tuple_type in [TRAINTUPLE_TYPE, AGGREGATETUPLE_TYPE]:
        end_model_file, end_model_file_hash = save_model(subtuple_directory, subtuple['key'])

    elif tuple_type == COMPOSITE_TRAINTUPLE_TYPE:
        end_head_model_file, end_head_model_file_hash = save_model(
            subtuple_directory,
            subtuple['key'],
            filename=output_head_model_filename,
        )
        end_trunk_model_file, end_trunk_model_file_hash = save_model(
            subtuple_directory,
            subtuple['key'],
            filename=output_trunk_model_filename,
        )

    # create result
    result = {}
    if tuple_type in (TRAINTUPLE_TYPE, AGGREGATETUPLE_TYPE):
        result['end_model_file_hash'] = end_model_file_hash
        result['end_model_file'] = end_model_file

    elif tuple_type == COMPOSITE_TRAINTUPLE_TYPE:
        result['end_head_model_file_hash'] = end_head_model_file_hash
        result['end_head_model_file'] = end_head_model_file
        result['end_trunk_model_file_hash'] = end_trunk_model_file_hash
        result['end_trunk_model_file'] = end_trunk_model_file

    # evaluation
    if tuple_type != TESTTUPLE_TYPE:  # skip evaluation
        return result

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
    result['global_perf'] = perf['all']
    return result


def save_model(subtuple_directory, subtuple_key, filename='model'):
    from substrapp.models import Model
    end_model_path = path.join(subtuple_directory, f'model/{filename}')
    end_model_file_hash = get_hash(end_model_path, subtuple_key)
    instance = Model.objects.create(pkhash=end_model_file_hash, validated=True)

    with open(end_model_path, 'rb') as f:
        instance.file.save('model', f)
    current_site = getattr(settings, "DEFAULT_DOMAIN")
    end_model_file = f'{current_site}{reverse("substrapp:model-file", args=[end_model_file_hash])}'

    return end_model_file, end_model_file_hash


def get_volume_id(compute_plan_id):
    org_name = getattr(settings, 'ORG_NAME')
    return f'local-{compute_plan_id}-{org_name}'


def get_subtuple_directory(subtuple):
    return path.join(getattr(settings, 'MEDIA_ROOT'), 'subtuple', subtuple['key'])

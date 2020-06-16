from __future__ import absolute_import, unicode_literals

from base64 import b64decode
import os
import shutil
import tempfile
from os import path
import json
import logging
import tarfile

import docker
import kubernetes

from django.conf import settings
from rest_framework.reverse import reverse
from celery.result import AsyncResult
from celery.exceptions import Ignore
from celery.task import Task
import boto3

from backend.celery import app
from substrapp.utils import (get_hash, get_owner, create_directory, uncompress_content, raise_if_path_traversal,
                             get_dir_hash, get_subtuple_directory, get_chainkeys_directory, timeit)
from substrapp.ledger_utils import (log_start_tuple, log_success_tuple, log_fail_tuple,
                                    query_tuples, LedgerError, LedgerStatusError, get_object_from_ledger)
from substrapp.tasks.utils import (compute_job, get_asset_content, get_and_put_asset_content,
                                   list_files, do_not_raise, ExceptionThread,
                                   remove_local_volume, get_or_create_local_volume, remove_image)

from substrapp.tasks.k8s_backend import copy_chainkeys_to_output_pvc
from substrapp.tasks.exception_handler import compute_error_code

logger = logging.getLogger(__name__)

PREFIX_HEAD_FILENAME = 'head_'
PREFIX_TRUNK_FILENAME = 'trunk_'

TRAINTUPLE_TYPE = 'traintuple'
AGGREGATETUPLE_TYPE = 'aggregatetuple'
COMPOSITE_TRAINTUPLE_TYPE = 'compositeTraintuple'
TESTTUPLE_TYPE = 'testtuple'

TUPLE_COMMANDS = {
    TRAINTUPLE_TYPE: 'train',
    TESTTUPLE_TYPE: 'predict',
    COMPOSITE_TRAINTUPLE_TYPE: 'train',
    AGGREGATETUPLE_TYPE: 'aggregate',
}

MODEL_FOLDER = '/sandbox/model'
OUTPUT_MODEL_FOLDER = '/sandbox/output_model'
OUTPUT_PERF_PATH = '/sandbox/perf/perf.json'
OUTPUT_HEAD_MODEL_FILENAME = 'head_model'
OUTPUT_TRUNK_MODEL_FILENAME = 'trunk_model'

TAG_VALUE_FOR_TRANSFER_BUCKET = "transferBucket"
ACCESS_KEY = os.getenv('BUCKET_TRANSFER_ID')
SECRET_KEY = os.getenv('BUCKET_TRANSFER_SECRET')
BUCKET_NAME = os.getenv('BUCKET_TRANSFER_NAME')
S3_PREFIX = os.getenv('BUCKET_TRANSFER_PREFIX')


class TasksError(Exception):
    pass


def get_objective(tuple_):

    objective_hash = tuple_['objective']['hash']
    objective_metadata = get_object_from_ledger(objective_hash, 'queryObjective')

    objective_content = get_asset_content(
        objective_metadata['metrics']['storageAddress'],
        objective_metadata['owner'],
        objective_metadata['metrics']['hash'],
    )

    return objective_content


@timeit
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


@timeit
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


def get_and_put_model_content(tuple_type, tuple_key, tuple_, out_model, model_dst_path):
    """Get out model content."""
    owner = tuple_get_owner(tuple_type, tuple_)
    return get_and_put_asset_content(
        out_model['storageAddress'],
        owner,
        out_model['hash'],
        content_dst_path=model_dst_path,
        salt=tuple_key
    )


def get_and_put_local_model_content(tuple_key, out_model, model_dst_path):
    """Get local model content."""
    from substrapp.models import Model

    model = Model.objects.get(pk=out_model['hash'])

    # verify that local db model file is not corrupted
    if get_hash(model.file.path, tuple_key) != out_model['hash']:
        raise Exception('Local Model Hash in Subtuple is not the same as in local db')

    if not os.path.exists(model_dst_path):
        os.symlink(model.file.path, model_dst_path)
    else:
        # verify that local subtuple model file is not corrupted
        if get_hash(model_dst_path, tuple_key) != out_model['hash']:
            raise Exception('Local Model Hash in Subtuple is not the same as in local medias')


@timeit
def fetch_model(parent_tuple_type, authorized_types, input_model, directory):

    tuple_type, metadata = find_training_step_tuple_from_key(input_model['traintupleKey'])

    if tuple_type not in authorized_types:
        raise TasksError(f'{parent_tuple_type.capitalize()}: invalid input model: type={tuple_type}')

    model_dst_path = path.join(directory, f'model/{input_model["traintupleKey"]}')
    raise_if_path_traversal([model_dst_path], path.join(directory, 'model/'))

    if tuple_type == TRAINTUPLE_TYPE:
        get_and_put_model_content(
            tuple_type, input_model['traintupleKey'], metadata, metadata['outModel'], model_dst_path
        )
    elif tuple_type == AGGREGATETUPLE_TYPE:
        get_and_put_model_content(
            tuple_type, input_model['traintupleKey'], metadata, metadata['outModel'], model_dst_path
        )
    elif tuple_type == COMPOSITE_TRAINTUPLE_TYPE:
        get_and_put_model_content(
            tuple_type, input_model['traintupleKey'], metadata, metadata['outTrunkModel']['outModel'], model_dst_path
        )
    else:
        raise TasksError(f'Traintuple: invalid input model: type={tuple_type}')


def fetch_models(tuple_type, authorized_types, input_models, directory):

    models = []

    for input_model in input_models:
        proc = ExceptionThread(target=fetch_model,
                               args=(tuple_type, authorized_types, input_model, directory))
        models.append(proc)
        proc.start()

    for proc in models:
        proc.join()

    exceptions = []

    for proc in models:
        if hasattr(proc, "_exception"):
            exceptions.append(proc._exception)
            logger.exception(proc._exception)
    else:
        if exceptions:
            raise Exception(exceptions)


def prepare_traintuple_input_models(directory, tuple_):
    """Get traintuple input models content."""
    input_models = tuple_.get('inModels')
    if not input_models:
        return

    authorized_types = (AGGREGATETUPLE_TYPE, TRAINTUPLE_TYPE)

    fetch_models(TRAINTUPLE_TYPE, authorized_types, input_models, directory)


def prepare_aggregatetuple_input_models(directory, tuple_):
    """Get aggregatetuple input models content."""
    input_models = tuple_.get('inModels')
    if not input_models:
        return

    authorized_types = (AGGREGATETUPLE_TYPE, TRAINTUPLE_TYPE, COMPOSITE_TRAINTUPLE_TYPE)

    fetch_models(AGGREGATETUPLE_TYPE, authorized_types, input_models, directory)


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
    head_model_dst_path = path.join(directory, f'model/{PREFIX_HEAD_FILENAME}{head_model_key}')
    raise_if_path_traversal([head_model_dst_path], path.join(directory, 'model/'))
    get_and_put_local_model_content(
        head_model_key, metadata['outHeadModel']['outModel'], head_model_dst_path
    )

    # get trunk model
    trunk_model_key = trunk_model['traintupleKey']
    tuple_type, metadata = find_training_step_tuple_from_key(trunk_model_key)
    trunk_model_dst_path = path.join(directory, f'model/{PREFIX_TRUNK_FILENAME}{trunk_model_key}')
    raise_if_path_traversal([trunk_model_dst_path], path.join(directory, 'model/'))
    # trunk model must refer to a composite traintuple or an aggregatetuple
    if tuple_type == COMPOSITE_TRAINTUPLE_TYPE:  # get output trunk model
        get_and_put_model_content(
            tuple_type, trunk_model_key, metadata, metadata['outTrunkModel']['outModel'], trunk_model_dst_path
        )
    elif tuple_type == AGGREGATETUPLE_TYPE:
        get_and_put_model_content(
            tuple_type, trunk_model_key, metadata, metadata['outModel'], trunk_model_dst_path
        )
    else:
        raise TasksError(f'CompositeTraintuple: invalid trunk input model: type={tuple_type}')


def prepare_testtuple_input_models(directory, tuple_):
    """Get testtuple input models content."""
    traintuple_type = tuple_['traintupleType']
    traintuple_key = tuple_['traintupleKey']

    # TODO we should use the find method to be consistent with the traintuple

    if traintuple_type == TRAINTUPLE_TYPE:
        metadata = get_object_from_ledger(traintuple_key, 'queryTraintuple')
        model_dst_path = path.join(directory, f'model/{traintuple_key}')
        raise_if_path_traversal([model_dst_path], path.join(directory, 'model/'))
        get_and_put_model_content(
            traintuple_type, traintuple_key, metadata, metadata['outModel'], model_dst_path
        )

    elif traintuple_type == COMPOSITE_TRAINTUPLE_TYPE:
        metadata = get_object_from_ledger(traintuple_key, 'queryCompositeTraintuple')
        head_model_dst_path = path.join(directory, f'model/{PREFIX_HEAD_FILENAME}{traintuple_key}')
        raise_if_path_traversal([head_model_dst_path], path.join(directory, 'model/'))
        get_and_put_local_model_content(traintuple_key, metadata['outHeadModel']['outModel'],
                                        head_model_dst_path)

        model_dst_path = path.join(directory, f'model/{PREFIX_TRUNK_FILENAME}{traintuple_key}')
        raise_if_path_traversal([model_dst_path], path.join(directory, 'model/'))
        get_and_put_model_content(
            traintuple_type, traintuple_key, metadata, metadata['outTrunkModel']['outModel'], model_dst_path
        )

    else:
        raise TasksError(f"Testtuple from type '{traintuple_type}' not supported")


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


@timeit
def prepare_opener(directory, tuple_):
    """Prepare opener for tuple execution."""
    from substrapp.models import DataManager
    data_opener_hash = tuple_['dataset']['openerHash']

    datamanager = DataManager.objects.get(pk=data_opener_hash)

    # verify that local storage opener file exists
    if not os.path.exists(datamanager.data_opener.path) or not os.path.isfile(datamanager.data_opener.path):
        raise Exception(f'DataOpener file ({datamanager.data_opener.path}) is missing in local storage')

    # verify that local db opener file is not corrupted
    if get_hash(datamanager.data_opener.path) != data_opener_hash:
        raise Exception('DataOpener Hash in Subtuple is not the same as in local db')

    opener_dst_path = path.join(directory, 'opener/__init__.py')
    if not os.path.exists(opener_dst_path):
        os.symlink(datamanager.data_opener.path, opener_dst_path)
    else:
        # verify that local subtuple data opener file is not corrupted
        if get_hash(opener_dst_path) != data_opener_hash:
            raise Exception('DataOpener Hash in Subtuple is not the same as in local medias')


@timeit
def prepare_data_sample(directory, tuple_):
    """Prepare data samples for tuple execution."""
    from substrapp.models import DataSample
    for data_sample_key in tuple_['dataset']['keys']:
        data_sample = DataSample.objects.get(pk=data_sample_key)

        if not os.path.exists(data_sample.path) or not os.path.isdir(data_sample.path):
            raise Exception(f'Data Sample ({data_sample.path}) is missing in local storage')

        if not os.listdir(data_sample.path):
            raise Exception(f'Data Sample ({data_sample.path}) is empty in local storage')

        data_sample_hash = get_dir_hash(data_sample.path)
        if data_sample_hash != data_sample_key:
            raise Exception('Data Sample Hash in tuple is not the same as in local db')

        # create a symlink on the folder containing data
        data_directory = path.join(directory, 'data', data_sample_key)
        try:
            if not os.path.exists(data_directory):
                os.symlink(data_sample.path, data_directory)

            if not (os.path.realpath(data_directory) == data_sample.path):
                Exception(f'Sym link ({data_directory})for tuple for data sample {data_sample.path}'
                          f'does not match (currently to {os.path.realpath(data_directory)}')
        except OSError as e:
            logger.exception(e)
            raise Exception('Failed to create sym link for tuple data sample')


def build_subtuple_folders(subtuple):
    # create a folder named `subtuple['key']` in /medias/subtuple/ with 5 subfolders opener, data, model, pred, metrics
    subtuple_directory = get_subtuple_directory(subtuple['key'])
    create_directory(subtuple_directory)

    for folder in ['opener', 'data', 'model', 'output_model', 'pred', 'perf', 'metrics', 'export']:
        create_directory(path.join(subtuple_directory, folder))

    return subtuple_directory


def remove_subtuple_materials(subtuple_directory):
    logger.info('Remove subtuple materials')
    list_files(subtuple_directory)
    try:
        shutil.rmtree(subtuple_directory)
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.exception(e)
    finally:
        if os.path.exists(subtuple_directory):
            list_files(subtuple_directory)


@timeit
def remove_local_folders(compute_plan_id):
    if not settings.ENABLE_REMOVE_LOCAL_CP_FOLDERS:
        logger.info(f'Skipping remove local volume of compute plan {compute_plan_id}')
        return

    logger.info(f'Remove local volume of compute plan {compute_plan_id}')

    volume_id = get_volume_id(compute_plan_id)

    remove_local_volume(volume_id)

    if settings.TASK['CHAINKEYS_ENABLED']:
        chainkeys_directory = get_chainkeys_directory(compute_plan_id)
        try:
            shutil.rmtree(chainkeys_directory)
        except Exception:
            logger.error(f'Cannot remove volume {chainkeys_directory}', exc_info=True)


@app.task(ignore_result=True)
def prepare_training_task():
    prepare_task(TRAINTUPLE_TYPE)


@app.task(ignore_result=True)
def prepare_testing_task():
    prepare_task(TESTTUPLE_TYPE)


@app.task(ignore_result=True)
def prepare_composite_training_task():
    prepare_task(COMPOSITE_TRAINTUPLE_TYPE)


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
        logger.exception(e)
        raise Ignore()

    compute_task.apply_async(
        (tuple_type, subtuple, compute_plan_id),
        queue=worker_queue)


class ComputeTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        from django.db import close_old_connections
        close_old_connections()

        tuple_type, subtuple, compute_plan_id = self.split_args(args)
        try:
            log_success_tuple(tuple_type, subtuple['key'], retval['result'])
        except LedgerError as e:
            logger.exception(e)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from django.db import close_old_connections
        close_old_connections()
        tuple_type, subtuple, compute_plan_id = self.split_args(args)

        try:
            error_code = compute_error_code(exc)
            # Do not show traceback if it's a container error as we already see them in
            # container log
            type_exc = type(exc)
            exc_info = not(type_exc == docker.errors.ContainerError)

            type_value = str(type_exc).split("'")[1]
            logger.error(f'{tuple_type} {subtuple["key"]} {error_code} - {type_value}',
                         exc_info=exc_info)
            log_fail_tuple(tuple_type, subtuple['key'], error_code)
        except LedgerError as e:
            logger.exception(e)

    def split_args(self, celery_args):
        tuple_type = celery_args[0]
        subtuple = celery_args[1]
        compute_plan_id = celery_args[2]
        return tuple_type, subtuple, compute_plan_id


@app.task(bind=True, acks_late=True, reject_on_worker_lost=True, ignore_result=False, base=ComputeTask)
# Ack late and reject on worker lost allows use to
# see http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-reject-on-worker-lost
# and https://github.com/celery/celery/issues/5106
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
                subtuple_directory = get_subtuple_directory(subtuple['key'])
                if os.path.exists(subtuple_directory):
                    remove_subtuple_materials(subtuple_directory)
            except Exception as e_removal:
                logger.exception(e_removal)

    return result


@timeit
def prepare_materials(subtuple, tuple_type):
    logger.info(f'Prepare materials for {tuple_type} task')

    # clean directory if exists (on retry)
    subtuple_directory = get_subtuple_directory(subtuple['key'])
    if os.path.exists(subtuple_directory):
        remove_subtuple_materials(subtuple_directory)

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

    logger.info(f'Prepare materials for {tuple_type} task: success')
    list_files(directory)


@timeit
def do_task(subtuple, tuple_type):
    subtuple_directory = get_subtuple_directory(subtuple['key'])
    org_name = getattr(settings, 'ORG_NAME')

    # compute plan / federated learning variables
    compute_plan_id = None
    rank = None
    compute_plan_tag = None

    if 'computePlanID' in subtuple and subtuple['computePlanID']:
        compute_plan_id = subtuple['computePlanID']
        rank = int(subtuple['rank'])
        compute_plan = get_object_from_ledger(compute_plan_id, 'queryComputePlan')
        compute_plan_tag = compute_plan['tag']

    return _do_task(
        subtuple_directory,
        tuple_type,
        subtuple,
        compute_plan_id,
        rank,
        org_name,
        compute_plan_tag,
    )


def _do_task(subtuple_directory, tuple_type, subtuple, compute_plan_id, rank, org_name, compute_plan_tag):

    common_volumes, compute_volumes = prepare_volumes(
        subtuple_directory, tuple_type, compute_plan_id, compute_plan_tag)

    # Add node index to environment variable for the compute
    node_index = os.getenv('NODE_INDEX')
    if node_index:
        environment = {'NODE_INDEX': node_index}
    else:
        environment = {}

    # Use tag to tranfer or not performances and models
    tag = subtuple.get("tag")
    if tuple_type == TESTTUPLE_TYPE:
        if tag and TAG_VALUE_FOR_TRANSFER_BUCKET in tag:
            environment['TESTTUPLE_TAG'] = TAG_VALUE_FOR_TRANSFER_BUCKET

    job_name = f'{tuple_type}-{subtuple["key"][0:8]}-{TUPLE_COMMANDS[tuple_type]}'.lower()
    command = generate_command(tuple_type, subtuple, rank)

    # train or predict
    compute_job(
        subtuple_key=subtuple["key"],
        dockerfile_path=subtuple_directory,
        image_name=get_algo_image_name(subtuple['algo']['hash']),
        job_name=job_name,
        volumes={**common_volumes, **compute_volumes},
        command=command,
        remove_image=not(compute_plan_id is not None or settings.TASK['CACHE_DOCKER_IMAGES']),
        remove_container=settings.TASK['CLEAN_EXECUTION_ENVIRONMENT'],
        capture_logs=settings.TASK['CAPTURE_LOGS'],
        environment=environment
    )

    # Handle model and result from tuple
    models = save_models(subtuple_directory, tuple_type, subtuple['key'])  # Can be empty if testtuple
    result = extract_result_from_models(tuple_type, models)  # Can be empty if testtuple

    # Evaluation
    if tuple_type == TESTTUPLE_TYPE:

        # We set pred folder to ro during evalutation
        pred_path = path.join(subtuple_directory, 'pred')
        common_volumes[pred_path]['mode'] = 'ro'

        # eval
        compute_job(
            subtuple_key=subtuple["key"],
            dockerfile_path=f'{subtuple_directory}/metrics',
            image_name=f'substra/metrics_{subtuple["key"][0:8]}'.lower(),
            job_name=f'{tuple_type}-{subtuple["key"][0:8]}-eval'.lower(),
            volumes=common_volumes,
            command=f'--output-perf-path {OUTPUT_PERF_PATH}',
            remove_image=not(settings.TASK['CACHE_DOCKER_IMAGES']),
            remove_container=settings.TASK['CLEAN_EXECUTION_ENVIRONMENT'],
            capture_logs=settings.TASK['CAPTURE_LOGS'],
            environment=environment
        )

        pred_path = path.join(subtuple_directory, 'pred')
        export_path = path.join(subtuple_directory, 'export')
        perf_path = path.join(subtuple_directory, 'perf')

        # load performance
        with open(path.join(perf_path, 'perf.json'), 'r') as perf_file:
            perf = json.load(perf_file)

        result['global_perf'] = perf['all']

        if tag and TAG_VALUE_FOR_TRANSFER_BUCKET in tag:
            transfer_to_bucket(subtuple['key'], [pred_path, perf_path, export_path])

    return result


@timeit
def prepare_volumes(subtuple_directory, tuple_type, compute_plan_id, compute_plan_tag):

    model_path = path.join(subtuple_directory, 'model')
    output_model_path = path.join(subtuple_directory, 'output_model')
    pred_path = path.join(subtuple_directory, 'pred')
    export_path = path.join(subtuple_directory, 'export')
    perf_path = path.join(subtuple_directory, 'perf')
    opener_path = path.join(subtuple_directory, 'opener')

    symlinks_volume = {}
    data_path = path.join(subtuple_directory, 'data')
    for subfolder in os.listdir(data_path):
        real_path = os.path.realpath(os.path.join(data_path, subfolder))
        symlinks_volume[real_path] = {'bind': f'{real_path}', 'mode': 'ro'}

    for subtuple_folder in ['opener', 'model', 'metrics']:
        for subitem in os.listdir(path.join(subtuple_directory, subtuple_folder)):
            real_path = os.path.realpath(os.path.join(subtuple_directory, subtuple_folder, subitem))
            if real_path != os.path.join(subtuple_directory, subtuple_folder, subitem):
                symlinks_volume[real_path] = {'bind': f'{real_path}', 'mode': 'ro'}

    volumes = {
        data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
        opener_path: {'bind': '/sandbox/opener', 'mode': 'ro'}
    }

    if tuple_type == TESTTUPLE_TYPE:
        volumes[pred_path] = {'bind': '/sandbox/pred', 'mode': 'rw'}
        volumes[export_path] = {'bind': '/sandbox/export', 'mode': 'rw'}
        volumes[perf_path] = {'bind': '/sandbox/perf', 'mode': 'rw'}

    model_volume = {
        model_path: {'bind': MODEL_FOLDER, 'mode': 'ro'},
        output_model_path: {'bind': OUTPUT_MODEL_FOLDER, 'mode': 'rw'}
    }

    # local volume for train like tuples in compute plan
    if compute_plan_id is not None:
        volume_id = get_volume_id(compute_plan_id)
        get_or_create_local_volume(volume_id)

        mode = 'ro' if tuple_type == TESTTUPLE_TYPE else 'rw'
        model_volume[volume_id] = {'bind': '/sandbox/local', 'mode': mode}

    chainkeys_volume = {}
    if compute_plan_id is not None and settings.TASK['CHAINKEYS_ENABLED']:
        chainkeys_volume = prepare_chainkeys(compute_plan_id, compute_plan_tag,
                                             subtuple_directory)

    return {**volumes, **symlinks_volume}, {**model_volume, **chainkeys_volume}


def prepare_chainkeys(compute_plan_id, compute_plan_tag, subtuple_directory):
    chainkeys_directory = get_chainkeys_directory(compute_plan_id)

    chainkeys_volume = {
        chainkeys_directory: {'bind': '/sandbox/chainkeys', 'mode': 'rw'}
    }

    if not os.path.exists(chainkeys_directory):
        os.makedirs(chainkeys_directory)

        kubernetes.config.load_incluster_config()
        k8s_client = kubernetes.client.CoreV1Api()

        secret_namespace = os.getenv('K8S_SECRET_NAMESPACE', 'default')
        label_selector = f'compute_plan={compute_plan_tag}'

        # fetch secrets and write them to disk
        try:
            secrets = k8s_client.list_namespaced_secret(secret_namespace, label_selector=label_selector)
        except kubernetes.client.rest.ApiException as e:
            logger.error(f'failed to fetch namespaced secrets {secret_namespace} with selector {label_selector}')
            raise e

        secrets = secrets.to_dict()['items']
        if not secrets:
            raise TasksError(f'No secret found using label selector {label_selector}')

        formatted_secrets = {
            s['metadata']['labels']['index']: list(b64decode(s['data']['key']))
            for s in secrets
        }

        with open(path.join(chainkeys_directory, 'chainkeys.json'), 'w') as f:
            json.dump({'chain_keys': formatted_secrets}, f)

        # remove secrets:
        # do not delete secrets as a running k8s operator will recreate them, instead
        # replace each secret data with an empty dict
        for secret in secrets:
            try:
                k8s_client.replace_namespaced_secret(
                    secret['metadata']['name'],
                    secret_namespace,
                    body=kubernetes.client.V1Secret(
                        data={},
                        metadata=kubernetes.client.V1ObjectMeta(
                            name=secret['metadata']['name'],
                            labels=secret['metadata']['labels'],
                        ),
                    ),
                )
            except kubernetes.client.rest.ApiException as e:
                logger.error(f'failed to remove secrets from namespace {secret_namespace}')
                raise e
        else:
            logger.info(f'{len(secrets)} secrets have been removed')

    list_files(chainkeys_directory)

    if settings.TASK['COMPUTE_BACKEND'] == 'k8s':
        copy_chainkeys_to_output_pvc(chainkeys_directory, subtuple_directory)
        list_files(subtuple_directory.replace('subtuple', 'outputs'))

    return chainkeys_volume


def generate_command(tuple_type, subtuple, rank):

    command = TUPLE_COMMANDS[tuple_type]

    if tuple_type == TRAINTUPLE_TYPE:

        if subtuple['inModels'] is not None:
            in_traintuple_keys = [subtuple_model["traintupleKey"] for subtuple_model in subtuple['inModels']]
            command = f"{command} {' '.join(in_traintuple_keys)}"

        command = f"{command} --output-model-path {OUTPUT_MODEL_FOLDER}/model"

        if rank is not None:
            command = f"{command} --rank {rank}"

    elif tuple_type == TESTTUPLE_TYPE:

        if COMPOSITE_TRAINTUPLE_TYPE == subtuple['traintupleType']:
            composite_traintuple_key = subtuple['traintupleKey']
            command = f"{command} --input-models-path {MODEL_FOLDER}"
            command = f"{command} --input-head-model-filename {PREFIX_HEAD_FILENAME}{composite_traintuple_key}"
            command = f"{command} --input-trunk-model-filename {PREFIX_TRUNK_FILENAME}{composite_traintuple_key}"
        else:
            in_model = subtuple["traintupleKey"]
            command = f'{command} {in_model}'

    elif tuple_type == COMPOSITE_TRAINTUPLE_TYPE:

        command = f"{command} --output-models-path {OUTPUT_MODEL_FOLDER}"
        command = f"{command} --output-head-model-filename {OUTPUT_HEAD_MODEL_FILENAME}"
        command = f"{command} --output-trunk-model-filename {OUTPUT_TRUNK_MODEL_FILENAME}"

        if subtuple['inHeadModel'] and subtuple['inTrunkModel']:
            command = f"{command} --input-models-path {MODEL_FOLDER}"

            in_head_model = subtuple['inHeadModel']
            in_head_model_key = in_head_model.get('traintupleKey')
            command = f"{command} --input-head-model-filename {PREFIX_HEAD_FILENAME}{in_head_model_key}"

            in_trunk_model = subtuple['inTrunkModel']
            in_trunk_model_key = in_trunk_model.get('traintupleKey')
            command = f"{command} --input-trunk-model-filename {PREFIX_TRUNK_FILENAME}{in_trunk_model_key}"

        if rank is not None:
            command = f"{command} --rank {rank}"

    elif tuple_type == AGGREGATETUPLE_TYPE:

        if subtuple['inModels'] is not None:
            in_aggregatetuple_keys = [subtuple_model["traintupleKey"] for subtuple_model in subtuple['inModels']]
            command = f"{command} {' '.join(in_aggregatetuple_keys)}"

        command = f"{command} --output-model-path {OUTPUT_MODEL_FOLDER}/model"

        if rank is not None:
            command = f"{command} --rank {rank}"

    return command


@do_not_raise
def transfer_to_bucket(tuple_key, paths):
    if not ACCESS_KEY or not SECRET_KEY or not BUCKET_NAME:
        logger.info(f'unset global env for bucket transter: {ACCESS_KEY} {SECRET_KEY} {BUCKET_NAME}')
        return

    with tempfile.TemporaryDirectory(prefix='/tmp/') as tmpdir:
        tar_name = f'{tuple_key}.tar.gz'
        tar_path = path.join(tmpdir, tar_name)
        with tarfile.open(tar_path, 'x:gz') as tar:
            for dir_path in paths:
                tar.add(dir_path)
        s3 = boto3.client(
            's3',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY)
        s3.upload_file(tar_path, BUCKET_NAME, f'{S3_PREFIX}/{tar_name}' if S3_PREFIX else tar_name)


@timeit
def save_models(subtuple_directory, tuple_type, subtuple_key):

    models = {}

    if tuple_type in [TRAINTUPLE_TYPE, AGGREGATETUPLE_TYPE]:
        file, file_hash = save_model(subtuple_directory, subtuple_key)
        models['end_model'] = {
            'file': file,
            'hash': file_hash
        }

    elif tuple_type == COMPOSITE_TRAINTUPLE_TYPE:

        for type_model, filename in [('end_head_model', OUTPUT_HEAD_MODEL_FILENAME),
                                     ('end_trunk_model', OUTPUT_TRUNK_MODEL_FILENAME)]:
            file, file_hash = save_model(
                subtuple_directory,
                subtuple_key,
                filename=filename,
            )

            models[type_model] = {
                'file': file,
                'hash': file_hash
            }

    return models


def extract_result_from_models(tuple_type, models):

    result = {}

    if tuple_type in (TRAINTUPLE_TYPE, AGGREGATETUPLE_TYPE):
        result['end_model_file'] = models['end_model']['file']
        result['end_model_file_hash'] = models['end_model']['hash']

    elif tuple_type == COMPOSITE_TRAINTUPLE_TYPE:
        # Head model does not expose storage address
        result['end_head_model_file_hash'] = models['end_head_model']['hash']

        result['end_trunk_model_file'] = models['end_trunk_model']['file']
        result['end_trunk_model_file_hash'] = models['end_trunk_model']['hash']

    return result


@timeit
def save_model(subtuple_directory, subtuple_key, filename='model'):
    from substrapp.models import Model

    end_model_path = path.join(subtuple_directory, f'output_model/{filename}')
    end_model_file_hash = get_hash(end_model_path, subtuple_key)
    instance = Model.objects.create(pkhash=end_model_file_hash, validated=True)

    with open(end_model_path, 'rb') as f:
        instance.file.save('model', f)
    current_site = getattr(settings, "DEFAULT_DOMAIN")
    end_model_file = f'{current_site}{reverse("substrapp:model-file", args=[end_model_file_hash])}'

    return end_model_file, end_model_file_hash


def get_volume_id(compute_plan_id, prefix='local'):
    org_name = getattr(settings, 'ORG_NAME')
    return f'{prefix}-{compute_plan_id}-{org_name}'


def get_algo_image_name(algo_hash):
    # tag must be lowercase for docker
    return f'substra/algo_{algo_hash[0:8]}'.lower()





def remove_algo_images(algo_hashes):
    for algo_hash in algo_hashes:
        algo_image_name = get_algo_image_name(algo_hash)

        remove_image(algo_image_name)


def remove_intermediary_models(model_hashes):
    from substrapp.models import Model

    models = Model.objects.filter(pkhash__in=model_hashes, validated=True)
    filtered_model_hashes = [model.pk for model in models]

    models.delete()

    log_model_hashes = '\n\t- '.join(filtered_model_hashes)
    logger.info(f'Remove intermediary models : \n\t- {log_model_hashes}')


@app.task(ignore_result=False)
def on_compute_plan(compute_plan):

    compute_plan_id = compute_plan['computePlanID']
    algo_hashes = compute_plan['algoKeys']
    model_hashes = compute_plan['modelsToDelete']
    status = compute_plan['status']

    # Remove local folder and algo when compute plan is finished
    if status in ['done', 'failed', 'canceled']:
        remove_local_folders(compute_plan_id)
        remove_algo_images(algo_hashes)

    # Remove intermediary models
    if model_hashes:
        remove_intermediary_models(model_hashes)

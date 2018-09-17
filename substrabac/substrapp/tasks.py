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
from .utils import compute_hash

import docker
import json


def create_directory(directory):
    if not path.exists(directory):
        os.makedirs(directory)


def get_hash(file):
    with open(file, 'rb') as f:
        data = f.read()
        return compute_hash(data)


def get_computed_hash(url):
    try:
        r = requests.get(url, headers={'Accept': 'application/json;version=0.0'})
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
    # Log Start TrainTest
    data, st = invokeLedger({
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["logFailTrainTest","%(key)s","%(err_msg)s"]}' % {'key': key, 'err_msg': err_msg}
    })

    if st != 201:
        # TODO log error
        pass

    return data


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

        if st == 200:
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
                    try:
                        content, computed_hash = get_remote_file(traintuple['algo'])
                    except:
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
                else:
                    algo_file_hash = get_hash(algo.file.path)
                    if algo_file_hash != traintuple['algo']['hash']:
                        return fail(traintuple['key'], 'Algo Hash in Traintuple is not the same as in local db')

                    try:
                        to_directory = path.join(getattr(settings, 'MEDIA_ROOT'), 'traintuple/%s' % (traintuple['key']))
                        copy(algo.file.path, to_directory)
                        tar_file_path = os.path.join(to_directory, os.path.basename(algo.file.name))
                        tar = tarfile.open(tar_file_path)
                        tar.extractall(to_directory)
                        tar.close()
                        os.remove(tar_file_path)
                    except:
                        return fail(traintuple['key'], 'Fail to untar algo file')

                # same for challenge metrics
                try:
                    challenge = Challenge.objects.get(pk=traintuple['challenge']['hash'])
                except Exception as e:
                    try:
                        content, computed_hash = get_remote_file(traintuple['challenge']['metrics'])
                    except:
                        return fail(traintuple['key'], e)
                    else:
                        to_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                                            'traintuple/%s/%s/%s' % (traintuple['key'], 'metrics', 'metrics.py'))
                        os.makedirs(os.path.dirname(to_path), exist_ok=True)
                        with open(to_path, 'wb') as f:
                            f.write(content)
                else:
                    challenge_metrics_hash = get_hash(challenge.metrics.path)
                    if challenge_metrics_hash != traintuple['challenge']['metrics']['hash']:
                        return fail(traintuple['key'], 'Challenge Hash in Traintuple is not the same as in local db')

                    copy(challenge.metrics.path,
                         path.join(getattr(settings, 'MEDIA_ROOT'),
                                   'traintuple/%s/%s' % (traintuple['key'], 'metrics')))

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
                        doTrainingTask.apply_async((traintuple, ), queue=settings.LEDGER['org']['org_name'])
                    except Exception as e:
                        return fail(traintuple['key'], e)
                elif data_type == 'testData':
                    try:
                        doTestingTask.apply_async((traintuple, ), queue=settings.LEDGER['org']['org_name'])
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
    from django.contrib.sites.models import Site
    from substrapp.models import Model

    # Setup Docker Client
    client = docker.from_env()

    # Docker variables
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
    try:
        client.images.build(path=algo_path,
                            tag=algo_docker,
                            rm=True)
    except Exception as e:
        return fail(traintuple['key'], e)

    # Run algo, train and make train predictions
    volumes = {train_data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
               train_pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
               model_path: {'bind': '/sandbox/model', 'mode': 'rw'},
               opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}
    try:
        client.containers.run(algo_docker,
                              name=algo_docker_name,
                              command='train',
                              volumes=volumes,
                              detach=False,
                              auto_remove=False,
                              remove=True)
    except Exception as e:
        return fail(traintuple['key'], e)

    # Build metrics
    try:
        client.images.build(path=path.join(getattr(settings, 'PROJECT_ROOT'), 'base_metrics'),
                            tag=metrics_docker,
                            rm=True)
    except Exception as e:
        return fail(traintuple['key'], e)

    # Compute metrics on train predictions
    volumes = {train_data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
               train_pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
               metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'},
               opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}
    try:
        client.containers.run(metrics_docker,
                              name=metrics_docker_name,
                              volumes=volumes,
                              detach=False,
                              auto_remove=False,
                              remove=True)
    except Exception as e:
        return fail(traintuple['key'], e)

    # Compute end model information
    end_model_path = path.join(getattr(settings, 'MEDIA_ROOT'),
                               'traintuple/%s/model/model' % (traintuple['key']))
    end_model_file_hash = get_hash(end_model_path)

    try:
        instance = Model.objects.create(pkhash=end_model_file_hash, validated=True)
        with open(end_model_path, 'rb') as f:
            instance.file.save('model', f)
    except Exception as e:
        return fail(traintuple['key'], e)

    url_http = 'http' if settings.DEBUG else 'https'
    current_site = Site.objects.get_current()
    end_model_file = '%s://%s%s' % (url_http, current_site.domain,
                                    reverse('substrapp:model-file', args=[end_model_file_hash]))

    # Load performance
    try:
        with open(os.path.join(train_pred_path, 'perf.json'), 'r') as perf_file:
            perf = json.load(perf_file)
        global_perf = perf['all']
    except Exception as e:
        return fail(traintuple['key'], e)

    # Log Success Train
    data, st = invokeLedger({
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["logSuccessTrain","%s","%s, %s","%s","Trained !"]}' % (traintuple['key'],
                                                                                 end_model_file_hash,
                                                                                 end_model_file,
                                                                                 global_perf)
    })

    return


@app.task
def doTestingTask(traintuple):
    # Setup Docker Client
    client = docker.from_env()

    # Docker variables
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
    try:
        client.images.build(path=algo_path,
                            tag=algo_docker,
                            rm=True)
    except Exception as e:
        return fail(traintuple['key'], e)

    # Run algo and make test predictions
    volumes = {test_data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
               test_pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
               model_path: {'bind': '/sandbox/model', 'mode': 'rw'},
               opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}
    try:
        client.containers.run(algo_docker,
                              name=algo_docker_name,
                              command='predict',
                              volumes=volumes,
                              detach=False,
                              auto_remove=False,
                              remove=True)
    except Exception as e:
        return fail(traintuple['key'], e)

    # Build metrics
    try:
        client.images.build(path=path.join(getattr(settings, 'PROJECT_ROOT'), 'base_metrics'),
                            tag=metrics_docker,
                            rm=True)
    except Exception as e:
        return fail(traintuple['key'], e)

    # Compute metrics on train predictions
    volumes = {test_data_path: {'bind': '/sandbox/data', 'mode': 'ro'},
               test_pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
               metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'},
               opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}
    try:
        client.containers.run(metrics_docker,
                              name=metrics_docker_name,
                              volumes=volumes,
                              detach=False,
                              auto_remove=False,
                              remove=True)
    except Exception as e:
        return fail(traintuple['key'], e)

    # Load performance
    try:
        with open(os.path.join(test_pred_path, 'perf.json'), 'r') as perf_file:
            perf = json.load(perf_file)
        global_perf = perf['all']
    except Exception as e:
        return fail(traintuple['key'], e)

    # Log Success Test
    data, st = invokeLedger({
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["logSuccessTest","%s","%s","Tested !"]}' % (traintuple['key'],
                                                                      global_perf)
    })

    return

import docker
import os
import re
import shutil
import tempfile

import requests
from django.conf import settings
from django.db import IntegrityError
from django.http import Http404
from django.urls import reverse
from docker.errors import ContainerError
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrabac.celery import app

from substrapp.models import Challenge
from substrapp.serializers import ChallengeSerializer, LedgerChallengeSerializer


from substrapp.utils import queryLedger, get_hash, get_computed_hash
from substrapp.tasks import build_subtuple_folders, remove_subtuple_materials
from substrapp.views.utils import get_filters, getObjectFromLedger, ComputeHashMixin, ManageFileMixin, JsonException


@app.task(bind=True, ignore_result=False)
def compute_dryrun(self, metrics_path, test_dataset_key, pkhash):

    try:
        subtuple_directory = build_subtuple_folders({'key': pkhash})

        metrics_path_dst = os.path.join(subtuple_directory, 'metrics/metrics.py')
        if not os.path.exists(metrics_path_dst):
            shutil.copy2(metrics_path, os.path.join(subtuple_directory, 'metrics/metrics.py'))
            os.remove(metrics_path)
        try:
            dataset = getObjectFromLedger(test_dataset_key, 'queryDataset')
        except JsonException as e:
            raise e
        else:
            opener_content, opener_computed_hash = get_computed_hash(dataset['opener']['storageAddress'])
            with open(os.path.join(subtuple_directory, 'opener/opener.py'), 'wb') as opener_file:
                opener_file.write(opener_content)

        # Launch verification
        client = docker.from_env()
        pred_path = os.path.join(subtuple_directory, 'pred')
        opener_file = os.path.join(subtuple_directory, 'opener/opener.py')
        metrics_file = os.path.join(subtuple_directory, 'metrics/metrics.py')
        metrics_path = os.path.join(getattr(settings, 'PROJECT_ROOT'), 'fake_metrics')   # base metrics comes with substrabac

        metrics_docker = 'metrics_dry_run'  # tag must be lowercase for docker
        metrics_docker_name = f'{metrics_docker}_{pkhash}'
        volumes = {pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
                   metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'},
                   opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

        client.images.build(path=metrics_path,
                            tag=metrics_docker,
                            rm=False)

        job_args = {'image': metrics_docker,
                    'name': metrics_docker_name,
                    'cpuset_cpus': '0-0',
                    'mem_limit': '1G',
                    'command': None,
                    'volumes': volumes,
                    'shm_size': '8G',
                    'labels': ['dryrun'],
                    'detach': False,
                    'auto_remove': False,
                    'remove': False}

        client.containers.run(**job_args)

        # Verify that the pred file exist
        assert os.path.exists(os.path.join(pred_path, 'perf.json'))

    except ContainerError as e:
        raise Exception(e.stderr)
    except Exception as e:
        raise str(e)
    finally:
        try:
            container = client.containers.get(metrics_docker_name)
            container.remove()
        except:
            pass
        remove_subtuple_materials(subtuple_directory)


class ChallengeViewSet(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       ComputeHashMixin,
                       ManageFileMixin,
                       GenericViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    query_call = 'queryChallenge'
    # permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        """
        Create a new Challenge \n
            TODO add info about what has to be posted\n
        - Example with curl (on localhost): \n
            curl -u username:password -H "Content-Type: application/json"\
            -X POST\
            -d '{"name": "tough challenge", "permissions": "all", "metrics_name": 'accuracy', "test_data":
            ["data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379",
            "data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389"],\
                "files": {"description.md": '#My tough challenge',\
                'metrics.py': 'def AUC_score(y_true, y_pred):\n\treturn 1'}}'\
                http://127.0.0.1:8000/substrapp/challenge/ \n
            Use double quotes for the json, simple quotes don't work.\n
        - Example with the python package requests (on localhost): \n
            requests.post('http://127.0.0.1:8000/challenge/',
                          #auth=('username', 'password'),
                          data={'name': 'MSI classification', 'permissions': 'all', 'metrics_name': 'accuracy', 'test_data_keys': ['da1bb7c31f62244c0f3a761cc168804227115793d01c270021fe3f7935482dcc']},
                          files={'description': open('description.md', 'rb'), 'metrics': open('metrics.py', 'rb')},
                          headers={'Accept': 'application/json;version=0.0'}) \n
        ---
        response_serializer: ChallengeSerializer
        """

        data = request.data

        dryrun = data.get('dryrun', False)

        description = data.get('description')
        test_dataset_key = data.get('test_dataset_key')
        test_data_keys = data.getlist('test_data_keys')
        metrics = data.get('metrics')

        pkhash = get_hash(description)
        serializer = self.get_serializer(data={'pkhash': pkhash,
                                               'metrics': metrics,
                                               'description': description})

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'message': e.args,
                             'pkhash': pkhash},
                            status=status.HTTP_400_BAD_REQUEST)
        else:

            if dryrun:
                try:
                    metrics_path = os.path.join(getattr(settings, 'DRYRUN_ROOT'), f'metrics_{pkhash}.py')
                    with open(metrics_path, 'wb') as metrics_file:
                        metrics_file.write(metrics.open().read())

                    task = compute_dryrun.apply_async((metrics_path, test_dataset_key, pkhash), queue=f"{settings.LEDGER['name']}.dryrunner")
                    url_http = 'http' if settings.DEBUG else 'https'
                    site_port = getattr(settings, "SITE_PORT", None)
                    current_site = f'{getattr(settings, "SITE_HOST")}'
                    if site_port:
                        current_site = f'{current_site}:{site_port}'
                    task_route = f'{url_http}://{current_site}{reverse("substrapp:task-detail", args=[task.id])}'
                    msg = f'Your dry-run has been taken in account. You can follow the task execution on {task_route}'
                except Exception as e:
                    return Response({'message': f'Could not launch challenge creation with dry-run on this instance: {str(e)}'},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'id': task.id, 'message': msg}, status=status.HTTP_202_ACCEPTED)

            # create on db
            try:
                instance = self.perform_create(serializer)
            except IntegrityError as exc:
                try:
                    pkhash = re.search('\(pkhash\)=\((\w+)\)', exc.args[0]).group(1)
                except:
                    pkhash = ''
                return Response({'message': 'A challenge with this description file already exists.', 'pkhash': pkhash},
                                status=status.HTTP_409_CONFLICT)
            except Exception as exc:
                return Response({'message': exc.args},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                # init ledger serializer
                ledger_serializer = LedgerChallengeSerializer(data={'test_data_keys': test_data_keys,
                                                                    'test_dataset_key': test_dataset_key,
                                                                    'name': data.get('name'),
                                                                    'permissions': data.get('permissions'),
                                                                    'metrics_name': data.get('metrics_name'),
                                                                    'instance': instance},
                                                              context={'request': request})

                if not ledger_serializer.is_valid():
                    # delete instance
                    instance.delete()
                    raise ValidationError(ledger_serializer.errors)

                # create on ledger
                data, st = ledger_serializer.create(ledger_serializer.validated_data)

                if st not in (status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED, status.HTTP_408_REQUEST_TIMEOUT):
                    return Response(data, status=st)

                headers = self.get_success_headers(serializer.data)
                d = dict(serializer.data)
                d.update(data)
                return Response(d, status=st, headers=headers)


    def create_or_update_challenge(self, challenge, pk):
        try:
            # get challenge description from remote node
            url = challenge['description']['storageAddress']
            try:
                r = requests.get(url, headers={'Accept': 'application/json;version=0.0'})  # TODO pass cert
            except:
                raise Exception(f'Failed to fetch {url}')
            else:
                if r.status_code != 200:
                    raise Exception(f'end to end node report {r.text}')

                try:
                    computed_hash = self.compute_hash(r.content)
                except Exception:
                    raise Exception('Failed to fetch description file')
                else:
                    if computed_hash != pk:
                        msg = 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'
                        raise Exception(msg)

                    f = tempfile.TemporaryFile()
                    f.write(r.content)

                    # save/update challenge in local db for later use
                    instance, created = Challenge.objects.update_or_create(pkhash=pk, validated=True)
                    instance.description.save('description.md', f)

        except Exception as e:
            raise e
        else:
            return instance

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        if len(pk) != 64:
            return Response({'message': f'Wrong pk {pk}'}, status.HTTP_400_BAD_REQUEST)

        try:
            int(pk, 16)  # test if pk is correct (hexadecimal)
        except:
            return Response({'message': f'Wrong pk {pk}'}, status.HTTP_400_BAD_REQUEST)
        else:
            # get instance from remote node
            try:
                data = getObjectFromLedger(pk, 'queryChallenge')
            except JsonException as e:
                return Response(e.msg, status=status.HTTP_400_BAD_REQUEST)
            else:
                error = None
                instance = None
                try:
                    # try to get it from local db to check if description exists
                    instance = self.get_object()
                except Http404:
                    try:
                        instance = self.create_or_update_challenge(data, pk)
                    except Exception as e:
                        error = e
                else:
                    # check if instance has description
                    if not instance.description:
                        try:
                            instance = self.create_or_update_challenge(data, pk)
                        except Exception as e:
                            error = e
                finally:
                    if error is not None:
                        return Response({'message': str(error)}, status=status.HTTP_400_BAD_REQUEST)

                    # do not give access to local files address
                    if instance is not None:
                        serializer = self.get_serializer(instance,
                                                         fields=('owner', 'pkhash', 'creation_date', 'last_modified'))
                        data.update(serializer.data)
                    else:
                        data = {'message': 'Fail to get instance'}

                    return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        # can modify result by interrogating `request.version`

        data, st = queryLedger({
            'args': '{"Args":["queryChallenges"]}'
        })
        datasetData = None
        algoData = None
        modelData = None

        # init list to return
        if data is None:
            data = []
        l = [data]

        if st == 200:

            # parse filters
            query_params = request.query_params.get('search', None)

            if query_params is not None:
                try:
                    filters = get_filters(query_params)
                except Exception as exc:
                    return Response(
                        {'message': f'Malformed search filters {query_params}'},
                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    # filtering, reset l to an empty array
                    l = []
                    for idx, filter in enumerate(filters):
                        # init each list iteration to data
                        l.append(data)
                        for k, subfilters in filter.items():
                            if k == 'challenge':  # filter by own key
                                for key, val in subfilters.items():
                                    if key == 'metrics':  # specific to nested metrics
                                        l[idx] = [x for x in l[idx] if x[key]['name'] in val]
                                    else:
                                        l[idx] = [x for x in l[idx] if x[key] in val]
                            elif k == 'dataset':  # select challenge used by these datasets
                                if not datasetData:
                                    # TODO find a way to put this call in cache
                                    datasetData, st = queryLedger({
                                        'args': '{"Args":["queryDatasets"]}'
                                    })
                                    if st != status.HTTP_200_OK:
                                        return Response(datasetData, status=st)
                                    if datasetData is None:
                                        datasetData = []

                                for key, val in subfilters.items():
                                    filteredData = [x for x in datasetData if x[key] in val]
                                    datasetKeys = [x['key'] for x in filteredData]
                                    challengeKeys = [x['challengeKey'] for x in filteredData]
                                    l[idx] = [x for x in l[idx] if x['key'] in challengeKeys or x['testData']['datasetKey'] in datasetKeys]
                            elif k == 'algo':  # select challenge used by these algo
                                if not algoData:
                                    # TODO find a way to put this call in cache
                                    algoData, st = queryLedger({
                                        'args': '{"Args":["queryAlgos"]}'
                                    })
                                    if st != status.HTTP_200_OK:
                                        return Response(algoData, status=st)
                                    if algoData is None:
                                        algoData = []

                                for key, val in subfilters.items():
                                    filteredData = [x for x in algoData if x[key] in val]
                                    challengeKeys = [x['challengeKey'] for x in filteredData]
                                    l[idx] = [x for x in l[idx] if x['key'] in challengeKeys]
                            elif k == 'model':  # select challenges used by outModel hash
                                if not modelData:
                                    # TODO find a way to put this call in cache
                                    modelData, st = queryLedger({
                                        'args': '{"Args":["queryTraintuples"]}'
                                    })
                                    if st != status.HTTP_200_OK:
                                        return Response(modelData, status=st)
                                    if modelData is None:
                                        modelData = []

                                for key, val in subfilters.items():
                                    filteredData = [x for x in modelData if x['outModel'] is not None and x['outModel'][key] in val]
                                    challengeKeys = [x['challenge']['hash'] for x in filteredData]
                                    l[idx] = [x for x in l[idx] if x['key'] in challengeKeys]

        return Response(l, status=st)

    @action(detail=True)
    def description(self, request, *args, **kwargs):
        return self.manage_file('description')

    @action(detail=True)
    def metrics(self, request, *args, **kwargs):
        return self.manage_file('metrics')

    @action(detail=True)
    def data(self, request, *args, **kwargs):
        instance = self.get_object()

        # TODO fetch list of data from ledger
        # query list of related algos and models from ledger

        # return success and model

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

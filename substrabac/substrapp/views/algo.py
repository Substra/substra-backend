import docker
import os
import tempfile
import tarfile


import requests
from django.conf import settings

from django.http import Http404
from docker.errors import ContainerError
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.reverse import reverse


from substrabac.celery import app

from substrapp.models import Algo
from substrapp.serializers import LedgerAlgoSerializer, AlgoSerializer
from substrapp.utils import queryLedger, get_hash, get_computed_hash
from substrapp.views.utils import get_filters, getObjectFromLedger, ComputeHashMixin, ManageFileMixin, JsonException
from substrapp.tasks import build_subtuple_folders, remove_subtuple_materials


@app.task(bind=True, ignore_result=False)
def compute_dryrun(self, algo_file, challenge_key, pkhash):
    from io import BytesIO

    try:
        subtuple_directory = build_subtuple_folders({'key': pkhash})

        tar = tarfile.open(fileobj=BytesIO(bytearray.fromhex(algo_file)))
        tar.extractall(subtuple_directory)
        tar.close()

        try:
            challenge = getObjectFromLedger(challenge_key)
        except JsonException as e:
            raise e
        else:
            metrics_content, metrics_computed_hash = get_computed_hash(challenge['metrics']['storageAddress'])
            with open(os.path.join(subtuple_directory, 'metrics/metrics.py'), 'wb') as metrics_file:
                metrics_file.write(metrics_content)
            dataset_key = challenge['testData']['datasetKey']

            try:
                dataset = getObjectFromLedger(dataset_key)
            except JsonException as e:
                raise e
            else:
                opener_content, opener_computed_hash = get_computed_hash(dataset['openerStorageAddress'])
                with open(os.path.join(subtuple_directory, 'opener/opener.py'), 'wb') as opener_file:
                    opener_file.write(opener_content)

                # Launch verification
                client = docker.from_env()
                opener_file = os.path.join(subtuple_directory, 'opener/opener.py')
                metrics_file = os.path.join(subtuple_directory, 'metrics/metrics.py')
                pred_path = os.path.join(subtuple_directory, 'pred')
                model_path = os.path.join(subtuple_directory, 'model')

                algo_docker = 'algo_dry_run'  # tag must be lowercase for docker
                algo_docker_name = f'{algo_docker}_{pkhash}'
                algo_path = subtuple_directory
                volumes = {pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
                           metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'},
                           opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'},
                           model_path: {'bind': '/sandbox/model', 'mode': 'rw'}}

                client.images.build(path=algo_path,
                                    tag=algo_docker,
                                    rm=True)

                job_args = {'image': algo_docker,
                            'name': algo_docker_name,
                            'cpuset_cpus': '0-1',
                            'mem_limit': '1G',
                            'command': '--dry-run',
                            'volumes': volumes,
                            'shm_size': '8G',
                            'labels': ['dryrun'],
                            'detach': False,
                            'auto_remove': False,
                            'remove': False}

                client.containers.run(**job_args)

    except ContainerError as e:
        raise Exception(e.stderr)
    except Exception as e:
        raise e
    finally:
        try:
            container = client.containers.get(algo_docker_name)
            container.remove()
            client.images.remove(algo_docker, force=True)
        except:
            pass
        remove_subtuple_materials(subtuple_directory)


class AlgoViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  ComputeHashMixin,
                  ManageFileMixin,
                  GenericViewSet):
    queryset = Algo.objects.all()
    serializer_class = AlgoSerializer

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = request.data

        dryrun = data.get('dryrun', False)

        file = data.get('file')
        challenge_key = data.get('challenge_key')
        pkhash = get_hash(file)
        serializer = self.get_serializer(data={
            'pkhash': pkhash,
            'file': file,
            'description': data.get('description')
        })

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({
                'message': e.args,
                'pkhash': pkhash
            },
                status=status.HTTP_400_BAD_REQUEST)
        else:

            if dryrun:
                try:
                    # TODO: DO NOT pass file content to celery tasks, use another strategy -> upload on remote nfs and pass path/url
                    task = compute_dryrun.apply_async((file.open().read().hex(), challenge_key, pkhash), queue=f"{settings.LEDGER['org']['name']}.dryrunner")
                    url_http = 'http' if settings.DEBUG else 'https'
                    current_site = f'{getattr(settings, "SITE_HOST")}:{getattr(settings, "SITE_PORT")}'
                    task_route = f'{url_http}://{current_site}{reverse("substrapp:task-detail", args=[task.id])}'
                    msg = f'Your dry-run has been taken in account. You can follow the task execution on {task_route}'
                except Exception as e:
                    return Response({'message': f'Could not launch algo creation with dry-run on this instance: {str(e)}'},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'id': task.id, 'message': msg}, status=status.HTTP_202_ACCEPTED)

            # create on db
            try:
                instance = self.perform_create(serializer)
            except Exception as exc:
                return Response({'message': exc.args},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                # init ledger serializer
                ledger_serializer = LedgerAlgoSerializer(data={'name': data.get('name'),
                                                               'permissions': data.get('permissions', 'all'),
                                                               'challenge_key': challenge_key,
                                                               'instance': instance},
                                                         context={'request': request})
                if not ledger_serializer.is_valid():
                    # delete instance
                    instance.delete()
                    raise ValidationError(ledger_serializer.errors)

                # create on ledger
                data, st = ledger_serializer.create(ledger_serializer.validated_data)

                if st not in [status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED]:
                    return Response(data, status=st)

                headers = self.get_success_headers(serializer.data)
                d = dict(serializer.data)
                d.update(data)
                return Response(d, status=st, headers=headers)

    def create_or_update_algo(self, algo, pk):
        try:
            # get challenge description from remote node
            url = algo['description']['storageAddress']
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
                    if computed_hash != algo['description']['hash']:
                        msg = 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'
                        raise Exception(msg)

                    f = tempfile.TemporaryFile()
                    f.write(r.content)

                    # save/update challenge in local db for later use
                    instance, created = Algo.objects.update_or_create(pkhash=pk, validated=True)
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
            error = None
            instance = None
            try:
                data = getObjectFromLedger(pk)
            except JsonException as e:
                return Response(e.msg, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    # try to get it from local db to check if description exists
                    instance = self.get_object()
                except Http404:
                    try:
                        instance = self.create_or_update_algo(data, pk)
                    except Exception as e:
                        error = e
                else:
                    # check if instance has description
                    if not instance.description:
                        try:
                            instance = self.create_or_update_algo(data, pk)
                        except Exception as e:
                            error = e
                finally:
                    if error is not None:
                        return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

                    # do not give access to local files address
                    if instance is not None:
                        serializer = self.get_serializer(instance, fields=('owner', 'pkhash', 'creation_date', 'last_modified'))
                        data.update(serializer.data)
                    else:
                        data = {'message': 'Fail to get instance'}

                    return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        # can modify result by interrogating `request.version`

        data, st = queryLedger({
            'args': '{"Args":["queryAlgos"]}'
        })
        challengeData = None
        datasetData = None
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
                    # filtering, reinit l to empty array
                    l = []
                    for idx, filter in enumerate(filters):
                        # init each list iteration to data
                        l.append(data)
                        for k, subfilters in filter.items():
                            if k == 'algo':  # filter by own key
                                for key, val in subfilters.items():
                                    l[idx] = [x for x in l[idx] if x[key] in val]
                            elif k == 'challenge':  # select challenge used by these datasets
                                st = None
                                if not challengeData:
                                    # TODO find a way to put this call in cache
                                    challengeData, st = queryLedger({
                                        'args': '{"Args":["queryChallenges"]}'
                                    })

                                    if st != status.HTTP_200_OK:
                                        return Response(challengeData, status=st)
                                    if challengeData is None:
                                        challengeData = []

                                for key, val in subfilters.items():
                                    if key == 'metrics':  # specific to nested metrics
                                        filteredData = [x for x in challengeData if x[key]['name'] in val]
                                    else:
                                        filteredData = [x for x in challengeData if x[key] in val]
                                    challengeKeys = [x['key'] for x in filteredData]
                                    l[idx] = [x for x in l[idx] if x['challengeKey'] in challengeKeys]
                            elif k == 'dataset':  # select challenge used by these algo
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
                                    challengeKeys = [x['challengeKey'] for x in filteredData]
                                    l[idx] = [x for x in l[idx] if x['challengeKey'] in challengeKeys]
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
                                    filteredData = [x for x in modelData if x['outModel'][key] in val]
                                    challengeKeys = [x['challenge']['hash'] for x in filteredData]
                                    l[idx] = [x for x in l[idx] if x['challengeKey'] in challengeKeys]

        return Response(l, status=st)

    @action(detail=True)
    def file(self, request, *args, **kwargs):
        return self.manage_file('file')

    @action(detail=True)
    def description(self, request, *args, **kwargs):
        return self.manage_file('description')

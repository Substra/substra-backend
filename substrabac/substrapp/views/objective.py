import docker
import logging
import os
import re
import shutil
import tempfile
import uuid

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

from substrapp.models import Objective
from substrapp.serializers import ObjectiveSerializer, LedgerObjectiveSerializer

from substrapp.ledger_utils import queryLedger, getObjectFromLedger
from substrapp.utils import get_hash, get_computed_hash, JsonException
from substrapp.tasks.tasks import build_subtuple_folders, remove_subtuple_materials
from substrapp.views.utils import ComputeHashMixin, ManageFileMixin, find_primary_key_error, validate_pk
from substrapp.views.filters_utils import filter_list


class ObjectiveViewSet(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       ComputeHashMixin,
                       ManageFileMixin,
                       GenericViewSet):
    queryset = Objective.objects.all()
    serializer_class = ObjectiveSerializer
    ledger_query_call = 'queryObjective'
    # permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        metrics = request.data.get('metrics')
        description = request.data.get('description')
        pkhash = get_hash(description)
        test_data_manager_key = request.data.get('test_data_manager_key', '')

        # try to serialize in local db to check that it is valid
        serializer = self.get_serializer(data={'pkhash': pkhash,
                                               'metrics': metrics,
                                               'description': description})
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            if find_primary_key_error(e):
                st = status.HTTP_409_CONFLICT
            else:
                st = status.HTTP_400_BAD_REQUEST
            return Response({'message': e.args, 'pkhash': pkhash}, status=st)

        # perform dry run if requested
        if request.data.get('dryrun', False):
            try:
                metrics_path = os.path.join(getattr(settings, 'DRYRUN_ROOT'), f'metrics_{pkhash}.py')
                with open(metrics_path, 'wb') as metrics_file:
                    metrics_file.write(metrics.open().read())
                task = compute_dryrun.apply_async(
                    (metrics_path, test_data_manager_key, pkhash),
                    queue=f"{settings.LEDGER['name']}.dryrunner"
                )
            except Exception as e:
                return Response({
                    'message': f'Could not launch objective creation with dry-run on this instance: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                current_site = getattr(settings, "DEFAULT_DOMAIN")
                task_route = f'{current_site}{reverse("substrapp:task-detail", args=[task.id])}'
                msg = f'Your dry-run has been taken in account. You can follow the task execution on {task_route}'

                return Response({'id': task.id, 'message': msg}, status=status.HTTP_202_ACCEPTED)

        # create on local db
        try:
            instance = self.perform_create(serializer)
        except IntegrityError as e:
            try:
                pkhash = re.search(r'\(pkhash\)=\((\w+)\)', e.args[0]).group(1)
            except IndexError:
                pkhash = ''
            return Response({'message': 'A objective with this description file already exists.', 'pkhash': pkhash},
                            status=status.HTTP_409_CONFLICT)
        except Exception as e:
            return Response({'message': e.args},
                            status=status.HTTP_400_BAD_REQUEST)

        # create on ledger db
        ledger_serializer = LedgerObjectiveSerializer(
            data={'test_data_sample_keys': request.data.getlist('test_data_sample_keys', []),
                  'test_data_manager_key': test_data_manager_key,
                  'name': request.data.get('name'),
                  'permissions': request.data.get('permissions'),
                  'metrics_name': request.data.get('metrics_name'),
                  'instance': instance},
            context={'request': request}
        )

        if not ledger_serializer.is_valid():
            instance.delete()
            raise ValidationError(ledger_serializer.errors)

        ledger_data, st = ledger_serializer.create(ledger_serializer.validated_data)

        if st not in (status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED, status.HTTP_408_REQUEST_TIMEOUT):
            return Response(ledger_data, status=st)

        # return response with local db and ledger data information
        headers = self.get_success_headers(serializer.data)
        data = dict(serializer.data)    # local db data
        data.update(ledger_data)   # ledger data
        return Response(data, status=st, headers=headers)

    def create_or_update_objective(self, objective, pk):

        # get description from remote node
        url = objective['description']['storageAddress']
        try:
            r = requests.get(url, headers={'Accept': 'application/json;version=0.0'})
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            raise Exception(f'Failed to fetch {url}')
        else:
            if r.status_code != status.HTTP_200_OK:
                raise Exception(f'end to end node report {r.text}')

        # verify description received has a good pkhash
        try:
            computed_hash = self.compute_hash(r.content)
        except Exception:
            raise Exception('Failed to fetch description file')
        else:
            if computed_hash != pk:
                msg = 'computed hash is not the same as the hosted file. ' \
                      'Please investigate for default of synchronization, corruption, or hacked'
                raise Exception(msg)

        # write objective with description in local db for later use
        tmp_description = tempfile.TemporaryFile()
        tmp_description.write(r.content)
        instance, created = Objective.objects.update_or_create(pkhash=pk, validated=True)
        instance.description.save('description.md', tmp_description)

        return instance

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            validate_pk(pk)
        except Exception as e:
            return Response({'message': str(e)}, status.HTTP_400_BAD_REQUEST)

        # get instance from remote node
        try:
            data = getObjectFromLedger(pk, self.ledger_query_call)
        except JsonException as e:
            return Response(e.msg, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            return Response(f'No element with key {pk}', status=status.HTTP_404_NOT_FOUND)

        # try to get it from local db to check if description exists
        try:
            instance = self.get_object()
        except Http404:
            instance = None

        if not instance or not instance.description:
            try:
                instance = self.create_or_update_objective(data, pk)
            except Exception as e:
                return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # For security reason, do not give access to local file address
        # Restrain data to some fields
        # TODO: do we need to send creation date and/or last modified date ?
        serializer = self.get_serializer(instance, fields=('owner', 'pkhash'))
        data.update(serializer.data)

        return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):

        data, st = queryLedger(fcn='queryObjectives', args=[])
        data = data if data else []

        objectives_list = [data]

        if st == status.HTTP_200_OK:
            query_params = request.query_params.get('search', None)
            if query_params is not None:
                try:
                    objectives_list = filter_list(
                        object_type='objective',
                        data=data,
                        query_params=query_params)
                except Exception as e:
                    logging.exception(e)
                    return Response(
                        {'message': f'Malformed search filters {query_params}'},
                        status=status.HTTP_400_BAD_REQUEST)

        return Response(objectives_list, status=st)

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

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@app.task(bind=True, ignore_result=False)
def compute_dryrun(self, metrics_path, test_data_manager_key, pkhash):

    dryrun_uuid = f'{pkhash}_{uuid.uuid4().hex}'

    subtuple_directory = build_subtuple_folders({'key': dryrun_uuid})

    metrics_path_dst = os.path.join(subtuple_directory, 'metrics/metrics.py')
    if not os.path.exists(metrics_path_dst):
        shutil.copy2(metrics_path, os.path.join(subtuple_directory, 'metrics/metrics.py'))
        os.remove(metrics_path)

    if not test_data_manager_key:
        raise Exception('Cannot do a objective dryrun without a data manager key.')

    datamanager = getObjectFromLedger(test_data_manager_key, 'queryDataManager')
    opener_content, opener_computed_hash = get_computed_hash(datamanager['opener']['storageAddress'])
    with open(os.path.join(subtuple_directory, 'opener/opener.py'), 'wb') as file:
        file.write(opener_content)

    # Launch verification
    client = docker.from_env()
    pred_path = os.path.join(subtuple_directory, 'pred')
    opener_file = os.path.join(subtuple_directory, 'opener/opener.py')
    metrics_file = os.path.join(subtuple_directory, 'metrics/metrics.py')
    metrics_path = os.path.join(getattr(settings, 'PROJECT_ROOT'), 'containers/dryrun_metrics')

    metrics_docker = 'metrics_dry_run'
    metrics_docker_name = f'{metrics_docker}_{dryrun_uuid}'
    volumes = {
        pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
        metrics_file: {'bind': '/sandbox/metrics/__init__.py', 'mode': 'ro'},
        opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

    client.images.build(path=metrics_path,
                        tag=metrics_docker,
                        rm=False)

    job_args = {
        'image': metrics_docker,
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

    try:
        client.containers.run(**job_args)
        if not os.path.exists(os.path.join(pred_path, 'perf.json')):
            raise Exception('Perf file not found')
    except ContainerError as e:
        raise Exception(e.stderr)
    finally:
        try:
            container = client.containers.get(metrics_docker_name)
            container.remove(force=True)
        except BaseException as e:
            logging.error(e, exc_info=True)

        remove_subtuple_materials(subtuple_directory)

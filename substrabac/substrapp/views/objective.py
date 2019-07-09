import docker
import logging
import os
import re
import shutil
import tempfile
import uuid

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

from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError, LedgerTimeout
from substrapp.utils import get_hash, get_computed_hash, get_from_node
from substrapp.tasks.tasks import build_subtuple_folders, remove_subtuple_materials
from substrapp.views.utils import ComputeHashMixin, ManageFileMixin, find_primary_key_error, validate_pk, \
    get_success_create_code, ValidationException, LedgerException
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

    def handle_dryrun(self, pkhash, metrics, test_data_manager_key):
        try:
            metrics_path = os.path.join(getattr(settings, 'DRYRUN_ROOT'), f'metrics_{pkhash}.py')
            with open(metrics_path, 'wb') as metrics_file:
                metrics_file.write(metrics.open().read())
            task = compute_dryrun.apply_async(
                (metrics_path, test_data_manager_key, pkhash),
                queue=f"{settings.LEDGER['name']}.dryrunner"
            )
        except Exception as e:
            raise Exception(f'Could not launch objective creation with dry-run on this instance: {str(e)}')
        else:
            current_site = getattr(settings, "DEFAULT_DOMAIN")
            task_route = f'{current_site}{reverse("substrapp:task-detail", args=[task.id])}'
            msg = f'Your dry-run has been taken in account. You can follow the task execution on {task_route}'

            return {'id': task.id, 'message': msg}

    def commit(self, serializer, request):
        # create on local db
        try:
            instance = self.perform_create(serializer)
        except IntegrityError as e:
            try:
                pkhash = re.search(r'\(pkhash\)=\((\w+)\)', e.args[0]).group(1)
            except IndexError:
                pkhash = ''
            err_msg = 'A objective with this description file already exists.'
            return {'message': err_msg, 'pkhash': pkhash}, status.HTTP_409_CONFLICT
        except Exception as e:
            raise Exception(e.args)

        # init ledger serializer
        ledger_data = {
            'test_data_sample_keys': request.data.getlist('test_data_sample_keys', []),
            'test_data_manager_key': request.data.get('test_data_manager_key', ''),
            'name': request.data.get('name'),
            'permissions': request.data.get('permissions'),
            'metrics_name': request.data.get('metrics_name'),
        }
        ledger_data.update({'instance': instance})
        ledger_serializer = LedgerObjectiveSerializer(data=ledger_data,
                                                      context={'request': request})

        if not ledger_serializer.is_valid():
            # delete instance
            instance.delete()
            raise ValidationError(ledger_serializer.errors)

        # create on ledger
        try:
            data = ledger_serializer.create(ledger_serializer.validated_data)
        except LedgerTimeout as e:
            data = {'pkhash': [x['pkhash'] for x in serializer.data], 'validated': False}
            raise LedgerException(data, e.status)
        except LedgerError as e:
            instance.delete()
            raise LedgerException(str(e.msg), e.status)
        except Exception:
            instance.delete()
            raise

        d = dict(serializer.data)
        d.update(data)

        return d

    def _create(self, request, dryrun):
        metrics = request.data.get('metrics')
        description = request.data.get('description')
        test_data_manager_key = request.data.get('test_data_manager_key', '')

        pkhash = get_hash(description)
        serializer = self.get_serializer(data={'pkhash': pkhash,
                                               'metrics': metrics,
                                               'description': description})

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            st = status.HTTP_400_BAD_REQUEST
            if find_primary_key_error(e):
                st = status.HTTP_409_CONFLICT
            raise ValidationException(e.args, pkhash, st)
        else:
            if dryrun:
                return self.handle_dryrun(pkhash, metrics, test_data_manager_key)

            # create on ledger + db
            return self.commit(serializer, request)

    def _get_create_status(self, dryrun):
        if dryrun:
            st = status.HTTP_202_ACCEPTED
        else:
            st = get_success_create_code()

        return st

    def create(self, request, *args, **kwargs):
        dryrun = request.data.get('dryrun', False)

        try:
            data = self._create(request, dryrun)
        except ValidationException as e:
            return Response({'message': e.data, 'pkhash': e.pkhash}, status=e.st)
        except LedgerException as e:
            return Response({'message': e.data}, status=e.st)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            headers = self.get_success_headers(data)
            st = self._get_create_status(dryrun)
            return Response(data, status=st, headers=headers)

    def create_or_update_objective(self, objective, pk):

        # get description from remote node
        url = objective['description']['storageAddress']

        response = get_from_node(url)

        # verify description received has a good pkhash
        try:
            computed_hash = self.compute_hash(response.content)
        except Exception:
            raise Exception('Failed to fetch description file')
        else:
            if computed_hash != pk:
                msg = 'computed hash is not the same as the hosted file. ' \
                      'Please investigate for default of synchronization, corruption, or hacked'
                raise Exception(msg)

        # write objective with description in local db for later use
        tmp_description = tempfile.TemporaryFile()
        tmp_description.write(response.content)
        instance, created = Objective.objects.update_or_create(pkhash=pk, validated=True)
        instance.description.save('description.md', tmp_description)

        return instance

    def _retrieve(self, pk):
        validate_pk(pk)
        # get instance from remote node
        data = get_object_from_ledger(pk, self.ledger_query_call)

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

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(pk)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        except Exception as e:
            return Response({'message': str(e)}, status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(fcn='queryObjectives', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        data = data if data else []

        objectives_list = [data]

        query_params = request.query_params.get('search', None)
        if query_params is not None:
            try:
                objectives_list = filter_list(
                    object_type='objective',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)
            except Exception as e:
                logging.exception(e)
                return Response(
                    {'message': f'Malformed search filters {query_params}'},
                    status=status.HTTP_400_BAD_REQUEST)

        return Response(objectives_list, status=status.HTTP_200_OK)

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

    datamanager = get_object_from_ledger(test_data_manager_key, 'queryDataManager')

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

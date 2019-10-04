import docker
import logging
import os
import re
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

from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError, LedgerTimeout, LedgerConflict
from substrapp.utils import get_hash, create_directory, uncompress_path
from substrapp.tasks.tasks import build_subtuple_folders, remove_subtuple_materials
from substrapp.tasks.utils import get_asset_content
from substrapp.views.utils import PermissionMixin, find_primary_key_error, validate_pk, \
    get_success_create_code, ValidationException, LedgerException, get_remote_asset, validate_sort
from substrapp.views.filters_utils import filter_list


def replace_storage_addresses(request, objective):
    objective['description']['storageAddress'] = request.build_absolute_uri(
        reverse('substrapp:objective-description', args=[objective['key']]))
    objective['metrics']['storageAddress'] = request.build_absolute_uri(
        reverse('substrapp:objective-metrics', args=[objective['key']])
    )


class ObjectiveViewSet(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       GenericViewSet):
    queryset = Objective.objects.all()
    serializer_class = ObjectiveSerializer
    ledger_query_call = 'queryObjective'

    def perform_create(self, serializer):
        return serializer.save()

    def handle_dryrun(self, pkhash, metrics, test_data_manager_key):
        try:
            dryrun_directory = os.path.join(getattr(settings, 'MEDIA_ROOT'), 'dryrun')
            create_directory(dryrun_directory)

            metrics_path = os.path.join(dryrun_directory, f'metrics_{pkhash}.archive')

            with open(metrics_path, 'wb') as fh:
                fh.write(metrics.open().read())
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
            # XXX workaround because input is a QueryDict and not a JSON object. This
            #     is due to the fact that we are sending file object and body in a
            #     single HTTP request
            'permissions': {
                'public': request.data.get('permissions_public'),
                'authorized_ids': request.data.getlist('permissions_authorized_ids', []),
            },
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
        except LedgerConflict as e:
            raise ValidationException(e.msg, e.pkhash, e.status)
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

        serializer = self.get_serializer(data={
            'pkhash': pkhash,
            'metrics': metrics,
            'description': description,
        })

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

        content = get_remote_asset(url, objective['owner'], pk)

        # write objective with description in local db for later use
        tmp_description = tempfile.TemporaryFile()
        tmp_description.write(content)
        instance, created = Objective.objects.update_or_create(pkhash=pk, validated=True)
        instance.description.save('description.md', tmp_description)

        return instance

    def _retrieve(self, request, pk):
        validate_pk(pk)
        # get instance from remote node
        data = get_object_from_ledger(pk, self.ledger_query_call)

        # try to get it from local db to check if description exists
        try:
            instance = self.get_object()
        except Http404:
            instance = None

        if not instance or not instance.description:
            instance = self.create_or_update_objective(data, pk)

        # For security reason, do not give access to local file address
        # Restrain data to some fields
        # TODO: do we need to send creation date and/or last modified date ?
        serializer = self.get_serializer(instance, fields=('owner', 'pkhash'))
        data.update(serializer.data)

        replace_storage_addresses(request, data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(request, pk)
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

        for group in objectives_list:
            for objective in group:
                replace_storage_addresses(request, objective)

        return Response(objectives_list, status=status.HTTP_200_OK)

    @action(detail=True)
    def data(self, request, *args, **kwargs):
        instance = self.get_object()

        # TODO fetch list of data from ledger
        # query list of related algos and models from ledger

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def leaderboard(self, request, pk):
        validate_pk(pk)

        sort = request.query_params.get('sort', 'desc')
        try:
            validate_sort(sort)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            leaderboard = query_ledger(fcn='queryObjectiveLeaderboard', args={
                'objectiveKey': pk,
                'ascendingOrder': sort == 'asc',
            })
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        return Response(leaderboard, status=status.HTTP_200_OK)


@app.task(bind=True, ignore_result=False)
def compute_dryrun(self, archive_path, test_data_manager_key, pkhash):
    if not test_data_manager_key:
        os.remove(archive_path)
        raise Exception('Cannot do an objective dryrun without a data manager key.')

    dryrun_uuid = f'{pkhash}_{uuid.uuid4().hex}'

    subtuple_directory = build_subtuple_folders({'key': dryrun_uuid})
    metrics_path = f'{subtuple_directory}/metrics'
    uncompress_path(archive_path, metrics_path)
    os.remove(archive_path)

    datamanager = get_object_from_ledger(test_data_manager_key, 'queryDataManager')
    opener_content = get_asset_content(
        datamanager['opener']['storageAddress'],
        datamanager['owner'],
        datamanager['opener']['hash'],
    )

    with open(os.path.join(subtuple_directory, 'opener/opener.py'), 'wb') as fh:
        fh.write(opener_content)

    # Launch verification
    client = docker.from_env()
    pred_path = os.path.join(subtuple_directory, 'pred')
    opener_file = os.path.join(subtuple_directory, 'opener/opener.py')

    metrics_docker = 'metrics_dry_run'
    metrics_docker_name = f'{metrics_docker}_{dryrun_uuid}'
    volumes = {
        pred_path: {'bind': '/sandbox/pred', 'mode': 'rw'},
        opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

    client.images.build(path=metrics_path,
                        tag=metrics_docker,
                        rm=False)

    job_args = {
        'image': metrics_docker,
        'name': metrics_docker_name,
        'cpuset_cpus': '0-0',
        'mem_limit': '1G',
        'command': '--dry-run',
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


class ObjectivePermissionViewSet(PermissionMixin,
                                 GenericViewSet):
    queryset = Objective.objects.all()
    serializer_class = ObjectiveSerializer
    ledger_query_call = 'queryObjective'

    @action(detail=True)
    def description(self, request, *args, **kwargs):
        return self.download_file(request, 'description')

    @action(detail=True)
    def metrics(self, request, *args, **kwargs):
        return self.download_file(request, 'metrics')

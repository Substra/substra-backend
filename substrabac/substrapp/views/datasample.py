import logging
from os.path import normpath

import docker
import os
import ntpath
import uuid

from checksumdir import dirhash
from django.conf import settings
from docker.errors import ContainerError
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.reverse import reverse

from substrabac.celery import app

from substrapp.models import DataSample, DataManager
from substrapp.serializers import DataSampleSerializer, LedgerDataSampleSerializer
from substrapp.serializers.ledger.datasample.util import updateLedgerDataSample
from substrapp.serializers.ledger.datasample.tasks import updateLedgerDataSampleAsync
from substrapp.utils import uncompress_path, get_dir_hash
from substrapp.tasks.tasks import build_subtuple_folders, remove_subtuple_materials
from substrapp.views.utils import find_primary_key_error, LedgerException, ValidationException, \
    get_success_create_code
from substrapp.ledger_utils import LedgerError, LedgerTimeout

logger = logging.getLogger('django.request')


class DataSampleViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        GenericViewSet):
    queryset = DataSample.objects.all()
    serializer_class = DataSampleSerializer

    def dryrun_task(self, data, data_manager_keys):
        task = compute_dryrun.apply_async((data, data_manager_keys),
                                          queue=f"{settings.LEDGER['name']}.dryrunner")
        current_site = getattr(settings, "DEFAULT_DOMAIN")
        task_route = f'{current_site}{reverse("substrapp:task-detail", args=[task.id])}'
        return task, f'Your dry-run has been taken in account. You can follow the task execution on {task_route}'

    @staticmethod
    def check_datamanagers(data_manager_keys):
        datamanager_count = DataManager.objects.filter(pkhash__in=data_manager_keys).count()

        if datamanager_count != len(data_manager_keys):
            raise Exception(f'One or more datamanager keys provided do not exist in local substrabac database. '
                            f'Please create them before. DataManager keys: {data_manager_keys}')

    @staticmethod
    def commit(serializer, ledger_data):
        instances = serializer.save()
        # init ledger serializer
        ledger_data.update({'instances': instances})
        ledger_serializer = LedgerDataSampleSerializer(data=ledger_data)

        if not ledger_serializer.is_valid():
            # delete instance
            for instance in instances:
                instance.delete()
            raise ValidationError(ledger_serializer.errors)

        # create on ledger
        try:
            data = ledger_serializer.create(ledger_serializer.validated_data)
        except LedgerTimeout as e:
            data = {'pkhash': [x['pkhash'] for x in serializer.data], 'validated': False}
            raise LedgerException(data, e.status)
        except LedgerError as e:
            for instance in instances:
                instance.delete()
            raise LedgerException(str(e.msg), e.status)
        except Exception:
            for instance in instances:
                instance.delete()
            raise

        st = get_success_create_code()

        # update validated to True in response
        if 'pkhash' in data and data['validated']:
            for d in serializer.data:
                if d['pkhash'] in data['pkhash']:
                    d.update({'validated': data['validated']})

        return serializer.data, st

    def compute_data(self, request):
        data = {}
        # files, should be archive
        for k, file in request.FILES.items():
            pkhash = get_dir_hash(file)  # can raise
            # check pkhash does not belong to the list
            try:
                existing = data[pkhash]
            except KeyError:
                pass
            else:
                raise Exception(f'Your data sample archives contain same files leading to same pkhash, '
                                f'please review the content of your achives. '
                                f'Archives {file} and {existing["file"]} are the same')
            data[pkhash] = {
                'pkhash': pkhash,
                'file': file
            }

        # path/paths case
        path = request.POST.get('path', None)
        paths = request.POST.getlist('paths', [])

        if path and paths:
            raise Exception('Cannot use path and paths together.')

        if path is not None:
            paths = [path]

        # paths, should be directories
        for path in paths:
            if not os.path.isdir(path):
                raise Exception(f'One of your paths does not exist, '
                                f'is not a directory or is not an absolute path: {path}')
            pkhash = dirhash(path, 'sha256')
            try:
                existing = data[pkhash]
            except KeyError:
                pass
            else:
                # existing can be a dict with a field path or file
                raise Exception(f'Your data sample directory contain same files leading to same pkhash. '
                                f'Invalid path: {path}.')

            data[pkhash] = {
                'pkhash': pkhash,
                'path': normpath(path)
            }

        if not data:  # data empty
            raise Exception(f'No data sample provided.')

        return list(data.values())

    def handle_dryrun(self, data, data_manager_keys):
        data_dry_run = []

        # write uploaded file to disk
        for d in data:
            pkhash = d['pkhash']
            if 'file' in d:
                file_path = os.path.join(getattr(settings, 'DRYRUN_ROOT'),
                                         f'data_{pkhash}.zip')
                with open(file_path, 'wb') as f:
                    f.write(d['file'].open().read())

                data_dry_run.append({
                    'pkhash': pkhash,
                    'file': file_path
                })

            if 'path' in d:
                data_dry_run.append(d)

        try:
            task, msg = self.dryrun_task(data_dry_run, data_manager_keys)
        except Exception as e:
            raise Exception(f'Could not launch data creation with dry-run on this instance: {str(e)}')
        else:
            return {'id': task.id, 'message': msg}, status.HTTP_202_ACCEPTED

    def _create(self, request, data_manager_keys, test_only, dryrun):

        if not data_manager_keys:
            raise Exception("missing or empty field 'data_manager_keys'")

        self.check_datamanagers(data_manager_keys)  # can raise

        computed_data = self.compute_data(request)

        serializer = self.get_serializer(data=computed_data, many=True)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            pkhashes = [x['pkhash'] for x in computed_data]
            st = status.HTTP_400_BAD_REQUEST
            if find_primary_key_error(e):
                st = status.HTTP_409_CONFLICT
            raise ValidationException(e.args, pkhashes, st)
        else:
            if dryrun:
                return self.handle_dryrun(computed_data, data_manager_keys)

            # create on ledger + db
            ledger_data = {'test_only': test_only,
                           'data_manager_keys': data_manager_keys}
            data, st = self.commit(serializer, ledger_data)
            return data, st

    def create(self, request, *args, **kwargs):
        dryrun = request.data.get('dryrun', False)
        test_only = request.data.get('test_only', False)
        data_manager_keys = request.data.getlist('data_manager_keys', [])

        try:
            data, st = self._create(request, data_manager_keys, test_only, dryrun)
        except ValidationException as e:
            return Response({'message': e.data, 'pkhash': e.pkhash}, status=e.st)
        except LedgerException as e:
            return Response({'message': e.data}, status=e.st)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            headers = self.get_success_headers(data)
            return Response(data, status=st, headers=headers)

    def validate_bulk_update(self, data):
        try:
            data_manager_keys = data.getlist('data_manager_keys')
        except KeyError:
            data_manager_keys = []
        if not data_manager_keys:
            raise Exception('Please pass a non empty data_manager_keys key param')

        try:
            data_sample_keys = data.getlist('data_sample_keys')
        except KeyError:
            data_sample_keys = []
        if not data_sample_keys:
            raise Exception('Please pass a non empty data_sample_keys key param')

        return data_manager_keys, data_sample_keys

    @action(methods=['post'], detail=False)
    def bulk_update(self, request):
        try:
            data_manager_keys, data_sample_keys = self.validate_bulk_update(request.data)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            args = {
                'hashes': ','.join(data_sample_keys),
                'dataManagerKeys': ','.join(data_manager_keys),
            }

            if getattr(settings, 'LEDGER_SYNC_ENABLED'):
                try:
                    data = updateLedgerDataSample(args, sync=True)
                except LedgerError as e:
                    return Response({'message': str(e.msg)}, status=e.st)

                st = status.HTTP_200_OK

            else:
                # use a celery task, as we are in an http request transaction
                updateLedgerDataSampleAsync.delay(args)
                data = {
                    'message': 'The substra network has been notified for updating these Data'
                }
                st = status.HTTP_202_ACCEPTED

            return Response(data, status=st)


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


@app.task(bind=True, ignore_result=False)
def compute_dryrun(self, data_samples, data_manager_keys):
    from shutil import copy
    from substrapp.models import DataManager

    client = docker.from_env()

    # Name of the dry-run subtuple (not important)
    pkhash = data_samples[0]['pkhash']
    dryrun_uuid = f'{pkhash}_{uuid.uuid4().hex}'
    subtuple_directory = build_subtuple_folders({'key': dryrun_uuid})
    data_path = os.path.join(subtuple_directory, 'data')
    volumes = {}

    try:
        for data_sample in data_samples:
            # uncompress only for file
            if 'file' in data_sample:
                uncompress_path(data_sample['file'], os.path.join(data_path, data_sample['pkhash']))
            # for all data paths, we need to create symbolic links inside data_path
            # and add real path to volume bind docker
            elif 'path' in data_sample:
                os.symlink(data_sample['path'], os.path.join(data_path, data_sample['pkhash']))
                volumes.update({
                    data_sample['path']: {'bind': data_sample['path'], 'mode': 'ro'}
                })

        for datamanager_key in data_manager_keys:
            datamanager = DataManager.objects.get(pk=datamanager_key)
            copy(datamanager.data_opener.path, os.path.join(subtuple_directory, 'opener/opener.py'))

            opener_file = os.path.join(subtuple_directory, 'opener/opener.py')
            data_sample_docker_path = os.path.join(getattr(settings, 'PROJECT_ROOT'), 'containers/dryrun_data_sample')

            data_docker = 'data_dry_run'
            data_docker_name = f'{data_docker}_{dryrun_uuid}'

            volumes.update({
                data_path: {'bind': '/sandbox/data', 'mode': 'rw'},
                opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}
            })

            client.images.build(path=data_sample_docker_path,
                                tag=data_docker,
                                rm=False)

            job_args = {
                'image': data_docker,
                'name': data_docker_name,
                'cpuset_cpus': '0-0',
                'mem_limit': '1G',
                'command': None,
                'volumes': volumes,
                'shm_size': '8G',
                'labels': ['dryrun'],
                'detach': False,
                'auto_remove': False,
                'remove': False,
            }

            client.containers.run(**job_args)

    except ContainerError as e:
        raise Exception(e.stderr)

    finally:
        try:
            container = client.containers.get(data_docker_name)
            container.remove()
        except Exception:
            logger.error('Could not remove containers')

        remove_subtuple_materials(subtuple_directory)

        for data_sample in data_samples:
            if 'file' in data_sample and os.path.exists(data_sample['file']):
                os.remove(data_sample['file'])

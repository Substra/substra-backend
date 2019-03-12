import docker
import os
import ntpath

from django.conf import settings
from docker.errors import ContainerError
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.reverse import reverse

from substrabac.celery import app

from substrapp.models import Data, Dataset
from substrapp.serializers import DataSerializer, LedgerDataSerializer
from substrapp.serializers.ledger.data.util import updateLedgerData
from substrapp.serializers.ledger.data.tasks import updateLedgerDataAsync
from substrapp.utils import get_hash, uncompress_path
from substrapp.tasks import build_subtuple_folders, remove_subtuple_materials


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class LedgerException(Exception):
    def __init__(self, data, st):
        self.data = data
        self.st = st
        super(LedgerException).__init__()


@app.task(bind=True, ignore_result=False)
def compute_dryrun(self, data_files, dataset_keys):
    from shutil import copy
    from substrapp.models import Dataset

    try:
        pkhash = data_files[0]['pkhash']
        subtuple_directory = build_subtuple_folders({'key': pkhash})

        for data in data_files:
            try:
                uncompress_path(data['filepath'],
                                os.path.join(subtuple_directory, 'data'))
            except Exception as e:
                raise e

        for dataset_key in dataset_keys:
            dataset = Dataset.objects.get(pk=dataset_key)
            copy(dataset.data_opener.path, os.path.join(subtuple_directory, 'opener/opener.py'))

            # Launch verification
            client = docker.from_env()
            opener_file = os.path.join(subtuple_directory, 'opener/opener.py')
            data_docker_path = os.path.join(getattr(settings, 'PROJECT_ROOT'), 'fake_data')   # fake_data comes with substrabac

            data_docker = 'data_dry_run'  # tag must be lowercase for docker
            data_docker_name = f'{data_docker}_{pkhash}'
            data_path = os.path.join(subtuple_directory, 'data')
            volumes = {data_path: {'bind': '/sandbox/data', 'mode': 'rw'},
                       opener_file: {'bind': '/sandbox/opener/__init__.py', 'mode': 'ro'}}

            client.images.build(path=data_docker_path,
                                tag=data_docker,
                                rm=False)

            job_args = {'image': data_docker,
                        'name': data_docker_name,
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

    except ContainerError as e:
        raise Exception(e.stderr)
    except Exception as e:
        raise str(e)
    finally:
        try:
            container = client.containers.get(data_docker_name)
            container.remove()
        except:
            pass
        remove_subtuple_materials(subtuple_directory)
        for data in data_files:
            if os.path.exists(data['filepath']):
                os.remove(data['filepath'])


class DataViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  # mixins.UpdateModelMixin,
                  # mixins.DestroyModelMixin,
                  # mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Data.objects.all()
    serializer_class = DataSerializer

    def dryrun_task(self, data_files, dataset_keys):
        task = compute_dryrun.apply_async((data_files, dataset_keys),
                                          queue=f"{settings.LEDGER['name']}.dryrunner")
        url_http = 'http' if settings.DEBUG else 'https'
        site_port = getattr(settings, "SITE_PORT", None)
        current_site = f'{getattr(settings, "SITE_HOST")}'
        if site_port:
            current_site = f'{current_site}:{site_port}'
        task_route = f'{url_http}://{current_site}{reverse("substrapp:task-detail", args=[task.id])}'
        return task, f'Your dry-run has been taken in account. You can follow the task execution on {task_route}'

    @staticmethod
    def check_datasets(dataset_keys):
        dataset_count = Dataset.objects.filter(pkhash__in=dataset_keys).count()

        if not len(dataset_keys) or dataset_count != len(dataset_keys):
            raise Exception(f'One or more dataset keys provided do not exist in local substrabac database. Please create them before. Dataset keys: {dataset_keys}')

    @staticmethod
    def commit(serializer, ledger_data, many):
        try:
            instances = serializer.save()
        except Exception as exc:
            raise exc
        else:
            # init ledger serializer
            if not many:
                instances = [instances]
            ledger_data.update({'instances': instances})
            ledger_serializer = LedgerDataSerializer(data=ledger_data)

            if not ledger_serializer.is_valid():
                # delete instance
                for instance in instances:
                    instance.delete()
                raise ValidationError(ledger_serializer.errors)

            # create on ledger
            data, st = ledger_serializer.create(
                ledger_serializer.validated_data)

            if st == status.HTTP_408_REQUEST_TIMEOUT:
                if many:
                    data.update({'pkhash': [x['pkhash'] for x in serializer.data]})
                raise LedgerException(data, st)

            if st not in (status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED):
                raise LedgerException(data, st)

            # update validated to True in response
            if 'pkhash' in data and data['validated']:
                if many:
                    for d in serializer.data:
                        if d['pkhash'] in data['pkhash']:
                            d.update({'validated': data['validated']})
                else:
                    d = dict(serializer.data)
                    d.update({'validated': data['validated']})

            return serializer.data, st

    def create(self, request, *args, **kwargs):
        data = request.data

        dryrun = data.get('dryrun', False)
        test_only = data.get('test_only', False)

        # check if bulk create
        dataset_keys = data.getlist('dataset_keys')

        try:
            self.check_datasets(dataset_keys)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            l = []
            for k, file in request.FILES.items():
                l.append({
                    'pkhash': get_hash(file),
                    'file': file
                })

            many = len(request.FILES) > 1
            data = l
            if not many:
                data = data[0]
            serializer = self.get_serializer(data=data, many=many)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                return Response({
                    'message': e.args,
                    'pkhash': [x['pkhash'] for x in l]},
                    status=status.HTTP_409_CONFLICT)
            else:
                if dryrun:
                    try:
                        data_files = []
                        for k, file in request.FILES.items():
                            pkhash = get_hash(file)

                            data_path = os.path.join(getattr(settings, 'DRYRUN_ROOT'), f'data_{pkhash}.zip')
                            with open(data_path, 'wb') as data_file:
                                data_file.write(file.open().read())

                            data_files.append({
                                'pkhash': pkhash,
                                'filepath': data_path,
                            })

                        task, msg = self.dryrun_task(data_files, dataset_keys)
                    except Exception as e:
                        return Response({'message': f'Could not launch data creation with dry-run on this instance: {str(e)}'},
                                        status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({'id': task.id, 'message': msg},
                                        status=status.HTTP_202_ACCEPTED)
                # create on ledger + db
                ledger_data = {'test_only': test_only,
                               'dataset_keys': dataset_keys}
                try:
                    data, st = self.commit(serializer, ledger_data, many)
                except LedgerException as e:
                    return Response({'message': e.data}, status=e.st)
                except Exception as e:
                    return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    headers = self.get_success_headers(data)
                    return Response(data, status=st, headers=headers)

    @action(methods=['post'], detail=False)
    def bulk_update(self, request):

        data = request.data
        dataset_keys = data.getlist('dataset_keys')
        data_keys = data.getlist('data_keys')

        args = '"%(hashes)s", "%(datasetKeys)s"' % {
            'hashes': ','.join(data_keys),
            'datasetKeys': ','.join(dataset_keys),
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            data, st = updateLedgerData(args, sync=True)

            # patch status for update
            if st == status.HTTP_201_CREATED:
                st = status.HTTP_200_OK
            return Response(data, status=st)
        else:
            # use a celery task, as we are in an http request transaction
            updateLedgerDataAsync.delay(args)
            data = {
                'message': 'The substra network has been notified for updating these Data'
            }
            st = status.HTTP_202_ACCEPTED
            return Response(data, status=st)


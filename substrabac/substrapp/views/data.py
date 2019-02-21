import docker
import os
import zipfile
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
from substrapp.utils import get_hash, get_computed_hash, uncompress_content
from substrapp.tasks import build_subtuple_folders, remove_subtuple_materials


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


@app.task(bind=True, ignore_result=False)
def compute_dryrun(self, data_files, dataset_keys):
    from shutil import copy
    from substrapp.models import Dataset

    try:
        pkhash = data_files[0]['pkhash']
        subtuple_directory = build_subtuple_folders({'key': pkhash})

        for data in data_files:
            try:
                uncompress_content(bytearray.fromhex(data['file']),
                                   os.path.join(subtuple_directory, 'data'))
            except Exception as e:
                raise e

        for dataset_key in dataset_keys:
            dataset = Dataset.objects.get(pk=dataset_key)
            copy(dataset.data_opener.path, os.path.join(subtuple_directory, 'opener/opener.py'))

            # Launch verification
            client = docker.from_env()
            opener_file = os.path.join(subtuple_directory, 'opener/opener.py')
            data_docker_path = os.path.join(getattr(settings, 'PROJECT_ROOT'), 'fake_data')   # base metrics comes with substrabac

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


class DataViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  # mixins.UpdateModelMixin,
                  # mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Data.objects.all()
    serializer_class = DataSerializer

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = request.data

        dryrun = data.get('dryrun', False)

        # check if bulk create
        files = request.data.getlist('files', None)
        dataset_keys = data.getlist('dataset_keys')
        dataset_count = Dataset.objects.filter(pkhash__in=dataset_keys).count()

        # check all dataset exists
        if dataset_count != len(dataset_keys):
            return Response({
                'message': f'One or more dataset keys provided do not exist in local substrabac database. Please create them before. Dataset keys: {dataset_keys}'},
                status=status.HTTP_400_BAD_REQUEST)
        else:

            if dryrun:
                try:
                    if files:
                        data_files = []
                        for x in files:
                            file = request.FILES[path_leaf(x)]
                            data_files.append({
                                'pkhash': get_hash(file),
                                'file': file.open().read().hex(),
                            })
                    else:
                        file = data.get('file')
                        pkhash = get_hash(file)
                        data_files = [{
                            'pkhash': pkhash,
                            'file': file.open().read().hex(),
                        }]

                    # TODO: DO NOT pass file content to celery tasks, use another strategy -> upload on remote nfs and pass path/url
                    task = compute_dryrun.apply_async((data_files, dataset_keys), queue=f"{settings.LEDGER['org']['name']}.dryrunner")
                    url_http = 'http' if settings.DEBUG else 'https'
                    site_port = getattr(settings, "SITE_PORT", None)
                    current_site = f'{getattr(settings, "SITE_HOST")}'
                    if site_port:
                        current_site = f'{current_site}:{site_port}'
                    task_route = f'{url_http}://{current_site}{reverse("substrapp:task-detail", args=[task.id])}'
                    msg = f'Your dry-run has been taken in account. You can follow the task execution on {task_route}'
                except Exception as e:
                    return Response({'message': f'Could not launch data creation with dry-run on this instance: {str(e)}'},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'id': task.id, 'message': msg}, status=status.HTTP_202_ACCEPTED)

            # bulk
            if files:

                l = []
                for x in files:
                    file = request.FILES[path_leaf(x)]
                    l.append({
                        'pkhash': get_hash(file),
                        'file': file
                    })

                serializer = self.get_serializer(data=l, many=True)
                try:
                    serializer.is_valid(raise_exception=True)
                except Exception as e:
                    return Response({
                        'message': e.args,
                        'pkhash': [x['pkhash'] for x in l]},
                        status=status.HTTP_409_CONFLICT)
                else:
                    # create on db
                    try:
                        instances = self.perform_create(serializer)
                    except Exception as exc:
                        return Response({'message': exc.args},
                                        status=status.HTTP_400_BAD_REQUEST)
                    else:
                        # init ledger serializer
                        ledger_serializer = LedgerDataSerializer(data={'test_only': data.get('test_only', False),
                                                                       'dataset_keys': dataset_keys,
                                                                       'instances': instances},
                                                                 context={'request': request})

                        if not ledger_serializer.is_valid():
                            # delete instance
                            for instance in instances:
                                instance.delete()
                            raise ValidationError(ledger_serializer.errors)

                        # create on ledger
                        data, st = ledger_serializer.create(ledger_serializer.validated_data)

                        if st not in [status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED]:
                            return Response(data, status=st)

                        headers = self.get_success_headers(serializer.data)
                        for d in serializer.data:
                            if d['pkhash'] in data['pkhash'] and data['validated'] is not None:
                                d['validated'] = data['validated']
                        return Response(serializer.data, status=st, headers=headers)
            else:
                file = data.get('file')
                pkhash = get_hash(file)
                d = {
                    'pkhash': pkhash,
                    'file': file
                }
                serializer = self.get_serializer(data=d)

                try:
                    serializer.is_valid(raise_exception=True)
                except Exception as e:
                    return Response({
                        'message': e.args,
                        'pkhash': pkhash},
                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    # create on db
                    try:
                        instance = self.perform_create(serializer)
                    except Exception as exc:
                        return Response({'message': exc.args},
                                        status=status.HTTP_400_BAD_REQUEST)
                    else:
                        # init ledger serializer
                        ledger_serializer = LedgerDataSerializer(data={'test_only': data.get('test_only', False),
                                                                       'dataset_keys': dataset_keys,
                                                                       'instances': [instance]},
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


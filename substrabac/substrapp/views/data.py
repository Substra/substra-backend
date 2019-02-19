import ntpath

from django.conf import settings
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
from substrapp.utils import get_hash


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


@app.task(bind=True, ignore_result=False)
def dryrun():
    pass


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
                task = dryrun.apply_async(queue=settings.LEDGER['org']['name'])
                url_http = 'http' if settings.DEBUG else 'https'
                current_site = f'{getattr(settings, "SITE_HOST")}:{getattr(settings, "SITE_PORT")}'
                task_route = f'{url_http}://{current_site}{reverse("substrapp:task-get", args=[task.id])}'
                msg = f'Your dry-run has been taken in account. You can follow the task execution on {task_route}'
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


import ntpath
import os
import re

from django.db import IntegrityError
from rest_framework import status, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.models import Data, Dataset
from substrapp.serializers import DataSerializer, LedgerDataSerializer


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


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

        # check if bulk create
        files = request.data.getlist('files', None)
        # get pkhash of data_opener from name
        try:
            dataset = Dataset.objects.get(pkhash=data.get('dataset_key'))
        except:
            return Response({
                'message': 'This Dataset key: %s does not exist in local substrabac database.' % data.get(
                    'dataset_key')},
                status=status.HTTP_400_BAD_REQUEST)
        else:
            # bulk
            if files:
                serializer = self.get_serializer(data=[{'file': request.FILES[path_leaf(x)]} for x in files], many=True)
                serializer.is_valid(raise_exception=True)
                # create on db
                try:
                    instances = self.perform_create(serializer)
                except IntegrityError as exc:
                    try:
                        pkhash = re.search('\(pkhash\)=\((\w+)\)', exc.args[0]).group(1)
                    except:
                        pkhash = ''
                    return Response({'message': 'One of the Data you passed already exists in the substrabac local database. Please review your args.',
                                     'pkhash': pkhash},
                                    status=status.HTTP_409_CONFLICT)
                except Exception as exc:
                    return Response({'message': exc.args},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    # init ledger serializer
                    file_size = 0
                    for file in files:
                        try:
                            file_size += os.path.getsize(file)
                        except:
                            file_size += request.FILES[path_leaf(file)].size

                    ledger_serializer = LedgerDataSerializer(data={'test_only': data.get('test_only'),
                                                                   'size': file_size,
                                                                   'dataset_key': dataset.pk,
                                                                   'instances': instances},
                                                             context={'request': request})

                    if not ledger_serializer.is_valid():
                        # delete instance
                        for instance in instances:
                            instance.delete()
                        raise ValidationError(ledger_serializer.errors)

                    # create on ledger
                    data, st = ledger_serializer.create(ledger_serializer.validated_data)
                    headers = self.get_success_headers(serializer.data)

                    for d in serializer.data:
                        if d['pkhash'] in data['pkhash'] and data['validated'] is not None:
                            d['validated'] = data['validated']
                    return Response(serializer.data, status=st, headers=headers)
            else:
                # get pkhash of data_opener from name
                serializer = self.get_serializer(data={'file': data.get('file')})
                serializer.is_valid(raise_exception=True)

                # create on db
                try:
                    instance = self.perform_create(serializer)
                except IntegrityError as exc:
                    return Response({
                                        'message': 'A Data with these data values already exists.'},
                                    status=status.HTTP_409_CONFLICT)
                except Exception as exc:
                    return Response({'message': exc.args},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    # init ledger serializer
                    file_size = 0
                    try:
                        file_size = os.path.getsize(data.get('file'))
                    except:
                        file_size = data.get('file').size

                    ledger_serializer = LedgerDataSerializer(data={'test_only': data.get('test_only'),
                                                                   'size': file_size,
                                                                   'dataset_key': dataset.pk,
                                                                   'instances': [instance]},
                                                             context={'request': request})

                    if not ledger_serializer.is_valid():
                        # delete instance
                        instance.delete()
                        raise ValidationError(ledger_serializer.errors)

                    # create on ledger
                    data, st = ledger_serializer.create(ledger_serializer.validated_data)
                    headers = self.get_success_headers(serializer.data)

                    d = dict(serializer.data)
                    d.update(data)
                    return Response(d, status=st, headers=headers)

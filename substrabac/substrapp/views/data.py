import os

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from substrapp.models import Data, Dataset
from substrapp.serializers import DataSerializer, LedgerDataSerializer


# TODO method to bulk_create data

class DataViewSet(ModelViewSet):
    queryset = Data.objects.all()
    serializer_class = DataSerializer

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = request.data

        # get pkhash of data_opener from name
        try:
            dataset = Dataset.objects.get(pkhash=data.get('dataset_key'))
        except:
            return Response({'message': 'This Dataset name does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:

            serializer = self.get_serializer(data={'file': data.get('file')})

            serializer.is_valid(raise_exception=True)

            # create on db
            instance = self.perform_create(serializer)

            # init ledger serializer
            file_size = 0
            try:
                file_size = os.path.getsize(data.get('file'))
            except:
                file_size = data.get('file').size

            ledger_serializer = LedgerDataSerializer(data={'test_only': data.get('test_only'),
                                                           'size': file_size,
                                                           'dataset_key': dataset.pkhash,
                                                           'instance': instance},
                                                     context={'request': request})

            if not ledger_serializer.is_valid():
                # delete instance
                instance.delete()
                raise ValidationError(ledger_serializer.errors)

            # create on ledger
            data, st = ledger_serializer.create(ledger_serializer.validated_data)

            headers = self.get_success_headers(serializer.data)

            data.update(serializer.data)
            return Response(data, status=st, headers=headers)

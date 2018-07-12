import os

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from substrapp.models import Data, Dataset
from substrapp.serializers import DataSerializer, LedgerDataSerializer


class DataViewSet(ModelViewSet):
    queryset = Data.objects.all()
    serializer_class = DataSerializer

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = request.data

        # get pkhash of data_opener from name
        try:
            dataset = Dataset.objects.get(pkhash=data['dataset_key'])
        except:
            return Response({'message': 'This Dataset name does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:

            serializer = self.get_serializer(data={'file': data.get('file')})

            serializer.is_valid(raise_exception=True)

            # create on db
            instance = self.perform_create(serializer)

            # init ledger serializer
            ledger_serializer = LedgerDataSerializer(data={'test_only': data.get('test_only'),
                                                           'size': os.path.getsize(data.get('file')),
                                                           'dataset_key': dataset.pkhash,
                                                           'instance': instance})

            if not ledger_serializer.is_valid():
                # delete instance
                instance.delete()
                raise ValidationError(ledger_serializer.errors)

            # create on ledger
            data, st = ledger_serializer.create(ledger_serializer.validated_data)

            headers = {}
            if st == status.HTTP_201_CREATED:
                headers = self.get_success_headers(serializer.data)

            data.update(serializer.data)
            return Response(data, status=st, headers=headers)
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from substrapp.models import Data, DataOpener
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
            data_opener = DataOpener.objects.get(name=data['data_opener'])
        except:
            return Response({'message': 'This DataOpener name does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:

            serializer = self.get_serializer(data={'features': data.get('features'),
                                                   'labels': data.get('labels')})

            serializer.is_valid(raise_exception=True)

            # create on db
            instance = self.perform_create(serializer)

            # init ledger serializer
            ledger_serializer = LedgerDataSerializer(data={'problems': data.getlist('problems'),
                                                           'name': data.get('name'),
                                                           'permissions': data.get('permissions', 'all'),
                                                           'data_opener': data_opener.pkhash,
                                                           'instance_pkhash': instance.pkhash})

            if not ledger_serializer.is_valid():
                # delete instance
                instance.delete()
                raise ValidationError(ledger_serializer.errors)

            # create on ledger
            ledger_serializer.create(serializer.validated_data)

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

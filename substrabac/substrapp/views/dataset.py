from django.db import IntegrityError
from rest_framework import status, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.conf import conf

# from hfc.fabric import Client
# cli = Client(net_profile="../network.json")
from substrapp.models import Dataset
from substrapp.serializers import DatasetSerializer, LedgerDatasetSerializer
from substrapp.utils import queryLedger


class DatasetViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     GenericViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer

    def list(self, request, *args, **kwargs):
        # can modify result by interrogating `request.version`

        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        data, st = queryLedger({
            'org': org,
            'peer': peer,
            'args': '{"Args":["queryAllDatasets"]}'
        })

        return Response(data, status=st)

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = request.data

        serializer = self.get_serializer(data={
            'data_opener': data.get('data_opener'),
            'description': data.get('description'),
            'name': data.get('name'),
        })

        serializer.is_valid(raise_exception=True)

        # create on db
        try:
            instance = self.perform_create(serializer)
        except IntegrityError as exc:
            return Response({'message': 'A dataset with this description file already exists.'},
                            status=status.HTTP_409_CONFLICT)
        else:
            # init ledger serializer
            ledger_serializer = LedgerDatasetSerializer(data={'name': data.get('name'),
                                                              'permissions': data.get('permissions'),
                                                              'type': data.get('type'),
                                                              'problem_keys': data.getlist('problem_keys'),
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

    # TODO create data list related to model
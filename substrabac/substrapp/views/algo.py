import json

from django.http import Http404
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.conf import conf
from substrapp.models import Algo, Challenge
from substrapp.serializers import LedgerAlgoSerializer, AlgoSerializer
from substrapp.utils import queryLedger


class AlgoViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Algo.objects.all()
    serializer_class = AlgoSerializer

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = request.data

        # get pkhash of challenge from name
        try:
            challenge = Challenge.objects.get(pkhash=data.get('challenge_key'))
        except:
            return Response({'message': 'This Challenge pkhash does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = self.get_serializer(data={'file': data.get('file'), 'description': data.get('description')})
            serializer.is_valid(raise_exception=True)

            # create on db
            instance = self.perform_create(serializer)

            # init ledger serializer
            ledger_serializer = LedgerAlgoSerializer(data={'name': data.get('name'),
                                                           'permissions': data.get('permissions', 'all'),
                                                           'challenge_key': challenge.pkhash,
                                                           'instance': instance},
                                                     context={'request': request})
            if not ledger_serializer.is_valid():
                # delete instance
                instance.delete()
                raise ValidationError(ledger_serializer.errors)

            # create on ledger
            data = ledger_serializer.create(ledger_serializer.validated_data)

            st = status.HTTP_201_CREATED
            headers = self.get_success_headers(serializer.data)

            data.update(serializer.data)
            return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):

        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        data, st = queryLedger({
            'org': org,
            'peer': peer,
            'args': '{"Args":["queryAlgos"]}'
        })

        return Response(data, status=st)

    @action(detail=True)
    def files(self, request, *args, **kwargs):
        # fetch algo from ledger
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            # try to get it from local db
            instance = self.get_object()
        except Http404:
            # get instance from remote node
            algo, st = queryLedger({
                'org': org,
                'peer': peer,
                'args': '{"Args":["queryObject","' + pk + '"]}'
            })
        finally:
            # TODO if requester has permission, return instance
            pass

        serializer = self.get_serializer(instance)
        return Response(serializer.data['file'])

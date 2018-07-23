from django.db import IntegrityError
from django.http import Http404
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.conf import conf
from substrapp.models import Model
from substrapp.serializers import ModelSerializer, LedgerChallengeSerializer

# from hfc.fabric import Client
# cli = Client(net_profile="../network.json")
from substrapp.utils import queryLedger


class ModelViewSet(mixins.ListModelMixin,
                   GenericViewSet):
    queryset = Model.objects.all()
    serializer_class = ModelSerializer

    # permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):

        # can modify result by interrogating `request.version`

        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        data, st = queryLedger({
            'org': org,
            'peer': peer,
            'args': '{"Args":["queryModels"]}'
        })

        return Response(data, status=st)


    # TODO create traintuples list related to model
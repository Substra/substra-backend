from django.http import Http404
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.conf import conf
from substrapp.models import Problem
from substrapp.serializers import ProblemSerializer, LedgerProblemSerializer

# from hfc.fabric import Client
# cli = Client(net_profile="../network.json")
from substrapp.views.utils import queryLedger

"""List all problems saved on local storage or submit a new one"""


class ProblemViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     GenericViewSet):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer

    # permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        """
        Create a new Problem \n
            TODO add info about what has to be posted\n
        - Example with curl (on localhost): \n
            curl -u username:password -H "Content-Type: application/json"\
            -X POST\
            -d '{"name": "tough problem", "test_data":
            ["data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379",
            "data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389"],\
                "files": {"description.md": '#My tough problem',\
                'metrics.py': 'def AUC_score(y_true, y_pred):\n\treturn 1'}}'\
                http://127.0.0.1:8000/substrapp/problem/ \n
            Use double quotes for the json, simple quotes don't work.\n
        - Example with the python package requests (on localhost): \n
            requests.post('http://127.0.0.1:8000/runapp/rawdata/',\
                          auth=('username', 'password'),\
                          json={'name': 'tough problem', 'test_data': '??',\
                        'files': {'iris.csv': 'bla', 'specific.py': 'bli'}})\n
        ---
        response_serializer: ProblemSerializer
        """

        data = request.data
        serializer = self.get_serializer(data={'metrics': data.get('metrics'),
                                               'description': data.get('description')})

        serializer.is_valid(raise_exception=True)

        # create on db
        instance = self.perform_create(serializer)

        # init ledger serializer
        ledger_serializer = LedgerProblemSerializer(data={'test_data': data.getlist('test_data'),
                                                          'name': data.get('name'),
                                                          'instance_pkhash': instance.pkhash})

        if not ledger_serializer.is_valid():
            # delete instance
            instance.delete()
            raise ValidationError(ledger_serializer.errors)

        # create on ledger
        ledger_serializer.create(ledger_serializer.validated_data)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):

        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        data, st = queryLedger({
            'org': org,
            'peer': peer,
            'args': '{"Args":["queryObjects", "problem"]}'
        })

        return Response(data, status=st)

    @action(detail=True)
    def metrics(self, request, *args, **kwargs):
        instance = self.get_object()

        # TODO fetch problem from ledger
        # if requester has permission, return metrics

        serializer = self.get_serializer(instance)
        return Response(serializer.data['metrics'])

    @action(detail=True)
    def leaderboard(self, request, *args, **kwargs):

        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            # try to get it from local db
            instance = self.get_object()
        except Http404:
            # get instance from remote node
            problem, st = queryLedger({
                'org': org,
                'peer': peer,
                'args': '{"Args":["queryObject","' + pk + '"]}'
            })

            # TODO check hash

            # TODO save problem in local db for later use
            #instance = Problem.objects.create(description=problem['description'], metrics=problem['metrics'])
        finally:
            # TODO query list of algos and models from ledger
            algos, _ = self.queryLedger({
                'org': org,
                'peer': peer,
                'args': '{"Args":["queryObjects", "algo"]}'
            })
            models, _ = self.queryLedger({
                'org': org,
                'peer': peer,
                'args': '{"Args":["queryObjects", "model"]}'
            })
            # TODO sort algos given the best perfs of their models

            # TODO return success, problem info, sorted algo + models

            #serializer = self.get_serializer(instance)
            return Response({
                'problem': problem,
                'algos': [x for x in algos if x['problem'] == pk],
                'models': models
            })

    @action(detail=True)
    def data(self, request, *args, **kwargs):
        instance = self.get_object()

        # TODO fetch list of data from ledger
        # query list of related algos and models from ledger

        # return success and model

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

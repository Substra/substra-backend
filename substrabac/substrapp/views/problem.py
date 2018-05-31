import json
import os
import sys
from subprocess import check_output, CalledProcessError, call

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

# from substrapp.util import switchToUserIdentity

# cli = Client(net_profile="../network.json")

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
        serializer = self.get_serializer(data={'metrics': data['metrics'],
                                               'description': data['description']})
        serializer.is_valid(raise_exception=True)

        # create on db
        instance = self.perform_create(serializer)

        # init ledger serializer
        ledger_serializer = LedgerProblemSerializer(data={'test_data': data.getlist('test_data'),
                                                          'name': data['name'],
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
        org_name = 'owkin'
        org = conf['orgs'][org_name]
        peer = org['peers'][0]

        # update config path for using right core.yaml
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../conf/' + org_name + '/' + peer['name'])
        print(cfg_path)
        os.environ['FABRIC_CFG_PATH'] = cfg_path

        channel_name = conf['misc']['channel_name']
        chaincode_name = conf['misc']['chaincode_name']

        print('Querying chaincode in the channel \'%(channel_name)s\' on the peer \'%(peer_host)s\' ...' % {
            'channel_name': channel_name,
            'peer_host': peer['host']
        }, flush=True)

        try:
            output = check_output(['../bin/peer',
                                   '--logging-level=debug',
                                   'chaincode', 'query',
                                   '-C', channel_name,
                                   '-n', chaincode_name,
                                   '-c', '{"Args":["queryObjects","problem"]}']).decode()
        except CalledProcessError as e:
            output = e.output.decode()
            # uncomment for debug
            print(output, flush=True)
            data = output
            st = status.HTTP_400_BAD_REQUEST
        else:
            try:
                value = output.split(': ')[1].replace('\n', '')
                value = json.loads(value)
            except:
                return output
            else:
                msg = 'Query of channel \'%(channel_name)s\' on peer \'%(peer_host)s\' was successful\n' % {
                    'channel_name': channel_name,
                    'peer_host': peer['host']
                }
                print(msg, flush=True)
                st = status.HTTP_200_OK
                data = value

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

        # TODO fetch problem from ledger

        try:
            # try to get it from local db
            instance = self.get_object()
        except Http404:
            # TODO get instance from remote node
            # check hash
            # save problem in local db for later use
            pass
        else:
            pass

            # TODO query list of algos and models from ledger

            # sort algos given the best perfs of their models

            # return success, problem info, sorted algo + models

            serializer = self.get_serializer(instance)
            return Response(serializer.data)

    @action(detail=True)
    def data(self, request, *args, **kwargs):
        instance = self.get_object()

        # TODO fetch list of data from ledger
        # query list of related algos and models from ledger

        # return success and model

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

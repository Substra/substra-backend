from urllib.parse import urlparse

import itertools
import hashlib

import requests

from django.db import IntegrityError
from django.http import Http404
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.conf import conf
from substrapp.models import Challenge
from substrapp.models.utils import compute_hash
from substrapp.serializers import ChallengeSerializer, LedgerChallengeSerializer

# from hfc.fabric import Client
# cli = Client(net_profile="../network.json")
from substrapp.utils import queryLedger
from substrapp.views.utils import get_filters


class ChallengeViewSet(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       GenericViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer

    # permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        """
        Create a new Challenge \n
            TODO add info about what has to be posted\n
        - Example with curl (on localhost): \n
            curl -u username:password -H "Content-Type: application/json"\
            -X POST\
            -d '{"name": "tough challenge", "permissions": "all", "metrics_name": 'accuracy', "test_data":
            ["data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379",
            "data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389"],\
                "files": {"description.md": '#My tough challenge',\
                'metrics.py': 'def AUC_score(y_true, y_pred):\n\treturn 1'}}'\
                http://127.0.0.1:8000/substrapp/challenge/ \n
            Use double quotes for the json, simple quotes don't work.\n
        - Example with the python package requests (on localhost): \n
            requests.post('http://127.0.0.1:8000/challenge/',
                          #auth=('username', 'password'),
                          data={'name': 'MSI classification', 'permissions': 'all', 'metrics_name': 'accuracy', 'test_data_keys': ['data_da1bb7c31f62244c0f3a761cc168804227115793d01c270021fe3f7935482dcc']},
                          files={'description': open('description.md', 'rb'), 'metrics': open('metrics.py', 'rb')},
                          headers={'Accept': 'application/json;version=0.0'}) \n
        ---
        response_serializer: ChallengeSerializer
        """

        data = request.data
        serializer = self.get_serializer(data={'metrics': data.get('metrics'),
                                               'description': data.get('description')})

        serializer.is_valid(raise_exception=True)

        # create on db
        try:
            instance = self.perform_create(serializer)
        except IntegrityError as exc:
            return Response({'message': 'A challenge with this description file already exists.'},
                            status=status.HTTP_409_CONFLICT)
        else:
            # init ledger serializer
            ledger_serializer = LedgerChallengeSerializer(data={'test_data_keys': data.getlist('test_data_keys'),
                                                                'name': data.get('name'),
                                                                'permissions': data.get('permissions'),
                                                                'metrics_name': data.get('metrics_name'),
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

    def retrieve(self, request, *args, **kwargs):
        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        # get pkhash
        try:
            pkhash = pk  # TODO test if pk is correct
        except:
            return Response({'message': 'Wrong pk %s' % pk}, status.HTTP_400_BAD_REQUEST)
        else:
            instance = None
            try:
                # try to get it from local db
                instance = self.get_object()
            except Http404:
                # get instance from remote node
                challenge, st = queryLedger({
                    'org': org,
                    'peer': peer,
                    'args': '{"Args":["query","%s"]}' % pk
                })

                # check hash
                try:
                    r = requests.get(challenge['descriptionStorageAddress'])
                except:
                    return Response({'message': 'Failed to check hash due to failed description fetch file %s' % challenge['descriptionStorageAddress']}, status.HTTP_400_BAD_REQUEST)
                else:
                    if r.status_code == 200:
                        description_file = r.content

                        sha256_hash = hashlib.sha256()
                        if isinstance(description_file, str):
                            description_file = description_file.encode()
                        sha256_hash.update(description_file)
                        computedHash = sha256_hash.hexdigest()

                        if computedHash == pkhash:
                            # save challenge in local db for later use
                            instance = Challenge.objects.create(pkhash=pkhash,
                                                                description=challenge['descriptionStorageAddress'],
                                                                metrics=challenge['metrics']['storageAddress'],
                                                                validated=True)

                        return Response({'message': 'computedHash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'}, status.HTTP_400_BAD_REQUEST)
            finally:
                if instance is not None:
                    serializer = self.get_serializer(instance)
                    return Response(serializer.data)

    def list(self, request, *args, **kwargs):

        # can modify result by interrogating `request.version`

        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        data, st = queryLedger({
            'org': org,
            'peer': peer,
            'args': '{"Args":["queryChallenges"]}'
        })
        datasetData = None
        algoData = None
        modelData = None

        # parse filters
        query_params = request.query_params.get('search', None)
        l = [data]
        if query_params is not None:
            try:
                filters = get_filters(query_params)
            except Exception as exc:
                return Response({'message': 'Malformed search filters %(query_params)s' % {'query_params': query_params}}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # filtering, reset l to an empty array
                l = []
                for idx, filter in enumerate(filters):
                    # init each list iteration to data
                    l.append(data)
                    for k, subfilters in filter.items():
                        if k == 'challenge':  # filter by own key
                            for key, val in subfilters.items():
                                if key == 'metrics': # specific to nested metrics
                                    l[idx] = [x for x in l[idx] if x[key]['name'] in val]
                                else:
                                    l[idx] = [x for x in l[idx] if x[key] in val]
                        elif k == 'dataset':  # select challenge used by these datasets
                            if not datasetData:
                                # TODO find a way to put this call in cache
                                datasetData, st = queryLedger({
                                    'org': org,
                                    'peer': peer,
                                    'args': '{"Args":["queryDatasets"]}'
                                })
                            for key, val in subfilters.items():
                                filteredData = [x for x in datasetData if x[key] in val]
                                challengeKeys = list(itertools.chain.from_iterable([x['challengeKeys'] for x in filteredData]))
                                l[idx] = [x for x in l[idx] if x['key'] in challengeKeys]
                        elif k == 'algo':  # select challenge used by these algo
                            if not algoData:
                                # TODO find a way to put this call in cache
                                algoData, st = queryLedger({
                                    'org': org,
                                    'peer': peer,
                                    'args': '{"Args":["queryAlgos"]}'
                                })
                            for key, val in subfilters.items():
                                filteredData = [x for x in algoData if x[key] in val]
                                challengeKeys = [x['challengeKey'] for x in filteredData]
                                l[idx] = [x for x in l[idx] if x['key'] in challengeKeys]
                        elif k == 'model':  # select challenges used by endModel hash
                            if not modelData:
                                # TODO find a way to put this call in cache
                                modelData, st = queryLedger({
                                    'org': org,
                                    'peer': peer,
                                    'args': '{"Args":["queryModels"]}'
                                })
                            for key, val in subfilters.items():
                                filteredData = [x for x in modelData if x['endModel'][key] in val]
                                challengeKeys = [x['challenge']['hash'] for x in filteredData]
                                l[idx] = [x for x in l[idx] if x['key'] in challengeKeys]

        return Response(l, status=st)

    @action(detail=True)
    def metrics(self, request, *args, **kwargs):
        instance = self.get_object()

        # TODO fetch challenge from ledger
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
            challenge, st = queryLedger({
                'org': org,
                'peer': peer,
                'args': '{"Args":["queryObject","' + pk + '"]}'
            })

            # TODO check hash

            # TODO save challenge in local db for later use
            # instance = Challenge.objects.create(description=challenge['description'], metrics=challenge['metrics'])
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

            # TODO return success, challenge info, sorted algo + models

            # serializer = self.get_serializer(instance)
            return Response({
                'challenge': challenge,
                'algos': [x for x in algos if x['challenge'] == pk],
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

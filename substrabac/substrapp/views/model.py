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
from substrapp.views.utils import get_filters, computeHashMixin


class ModelViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   computeHashMixin,
                   GenericViewSet):
    queryset = Model.objects.all()
    serializer_class = ModelSerializer

    # permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        if len(pk) != 64:
            return Response({'message': 'Wrong pk %s' % pk}, status.HTTP_400_BAD_REQUEST)

        # get pkhash
        pkhash = pk
        try:
            int(pk, 16)  # test if pk is correct (hexadecimal)
        except:
            return Response({'message': 'Wrong pk %s' % pk}, status.HTTP_400_BAD_REQUEST)
        else:
            instance = None
            try:
                # try to get it from local db
                instance = self.get_object()
            except Http404:
                # get instance from remote node
                model, st = queryLedger({
                    'org': org,
                    'peer': peer,
                    'args': '{"Args":["queryModelTraintuples","%s"]}' % pk
                })

                try:
                    computed_hash = self.get_computed_hash(model['descriptionStorageAddress'])
                except Exception as e:
                    return Response({'message': 'Failed to fetch description file'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    if computed_hash == pkhash:
                        # save challenge in local db for later use
                        instance = Model.objects.create(pkhash=pkhash,
                                                        file=model['descriptionStorageAddress'],
                                                        validated=True)

                    return Response({
                        'message': 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'},
                        status.HTTP_400_BAD_REQUEST)
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
            'args': '{"Args":["queryTraintuples"]}'
        })
        algoData = None
        challengeData = None
        datasetData = None

        # parse filters
        query_params = request.query_params.get('search', None)
        l = [data]
        if query_params is not None:
            try:
                filters = get_filters(query_params)
            except Exception as exc:
                return Response(
                    {'message': 'Malformed search filters %(query_params)s' % {'query_params': query_params}},
                    status=status.HTTP_400_BAD_REQUEST)
            else:
                # filtering, reinit l to empty array
                l = []
                for idx, filter in enumerate(filters):
                    # init each list iteration to data
                    l.append(data)
                    for k, subfilters in filter.items():
                        if k == 'model':  # filter by own key
                            for key, val in subfilters.items():
                                l[idx] = [x for x in l[idx] if x['endModel']['hash'] in val]
                        elif k == 'algo':  # select model used by these algo
                            if not algoData:
                                # TODO find a way to put this call in cache
                                algoData, st = queryLedger({
                                    'org': org,
                                    'peer': peer,
                                    'args': '{"Args":["queryAlgos"]}'
                                })
                            for key, val in subfilters.items():
                                filteredData = [x for x in algoData if x[key] in val]
                                algoHashes = [x['key'] for x in filteredData]
                                l[idx] = [x for x in l[idx] if 'algo_%s' % x['algo']['hash'] in algoHashes]
                        elif k == 'dataset':  # select model which trainData.openerHash is
                            if not datasetData:
                                # TODO find a way to put this call in cache
                                datasetData, st = queryLedger({
                                    'org': org,
                                    'peer': peer,
                                    'args': '{"Args":["queryDatasets"]}'
                                })
                            for key, val in subfilters.items():
                                filteredData = [x for x in datasetData if x[key] in val]
                                datasetHashes = [x['key'] for x in filteredData]
                                l[idx] = [x for x in l[idx] if
                                          'dataset_%s' % x['trainData']['openerHash'] in datasetHashes]
                        elif k == 'challenge':  # select challenge used by these datasets
                            if not challengeData:
                                # TODO find a way to put this call in cache
                                challengeData, st = queryLedger({
                                    'org': org,
                                    'peer': peer,
                                    'args': '{"Args":["queryChallenges"]}'
                                })
                            for key, val in subfilters.items():
                                if key == 'metrics':  # specific to nested metrics
                                    filteredData = [x for x in challengeData if x[key]['name'] in val]
                                else:
                                    filteredData = [x for x in challengeData if x[key] in val]
                                challengeKeys = [x['key'] for x in filteredData]
                                l[idx] = [x for x in l[idx] if 'challenge_%s' % x['challenge']['hash'] in challengeKeys]

        return Response(l, status=st)

    @action(methods=['post'], detail=False)
    def create_traintuple(self, request):
        '''
        curl -H "Accept: text/html;version=0.0, */*;version=0.0"
         -d "challenge_key=eb0295d98f37ae9e95102afae792d540137be2dedf6c4b00570ab1d1f355d033&algo_key=082f972d09049fdb7e34659f6fea82c5082be717cc9dab89bb92f620e6517106&startModel_key=082f972d09049fdb7e34659f6fea82c5082be717cc9dab89bb92f620e6517106&train_data[]=aa1bb7c31f62244c0f3a761cc168804227115793d01c270021fe3f7935482dcc&train_data[]=aa2bb7c31f62244c0f3a761cc168804227115793d01c270021fe3f7935482dcc"
          -X POST http://localhost:8000/model/create_traintuple/

        or

        curl -H "Accept: text/html;version=0.0, */*;version=0.0" -H "Content-Type: application/json"
        -d '{"challenge_key":"eb0295d98f37ae9e95102afae792d540137be2dedf6c4b00570ab1d1f355d033","algo_key":"082f972d09049fdb7e34659f6fea82c5082be717cc9dab89bb92f620e6517106","startModel_key":"082f972d09049fdb7e34659f6fea82c5082be717cc9dab89bb92f620e6517106","train_data":["aa1bb7c31f62244c0f3a761cc168804227115793d01c270021fe3f7935482dcc","aa2bb7c31f62244c0f3a761cc168804227115793d01c270021fe3f7935482dcc"]}'
         -X POST http://localhost:8000/model/create_traintuple/?format=json

        :param request:
        :return:
        '''

        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        try:
            challenge_key = request.data.get('challenge_key', request.POST.get('challenge_key', None))
            algo_key = request.data.get('algo_key', request.POST.get('algo_key', None))
            startModel_key = request.data.get('startModel_key', request.POST.get('startModel_key', None))
            try:
                train_data = request.data.getlist('train_data', [])
            except:
                train_data = request.data.get('train_data', request.POST.getlist('train_data', []))
        except:
            return Response({'message': 'Check the way you pass your parameters'})

        if challenge_key is not None and algo_key is not None and startModel_key is not None:
            data, st = queryLedger({
                'org': org,
                'peer': peer,
                'args': '{"Args":["createTraintuple","%(challenge_key)s","%(algo_key)s","%(startModel_key)s","%(train_data)s"]}' % {
                    'challenge_key': challenge_key,
                    'algo_key': algo_key,
                    'startModel_key': startModel_key,
                    'train_data': ','.join(train_data)}
            })

            if st == 200:
                return Response({'traintuple': data}, status=st)
            return Response(data, status=st)

        return Response({'message': 'Wrong parameters passed. Please refer to documentation.'})
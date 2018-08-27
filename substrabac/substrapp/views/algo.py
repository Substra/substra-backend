import hashlib
import itertools

import requests
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
from substrapp.views.utils import get_filters, computeHashMixin


class AlgoViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  computeHashMixin,
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

    def retrieve(self, request, *args, **kwargs):
        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        if len(pk) != 64:
            return Response({'message': 'Wrong pk %s' % pk}, status.HTTP_400_BAD_REQUEST)

        # get pkhash
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
                algo, st = queryLedger({
                    'org': org,
                    'peer': peer,
                    'args': '{"Args":["query","%s"]}' % pk
                })
                if st != 200:
                    return Response(algo, status=st)

                try:
                    computed_hash = self.get_computed_hash(algo['description']['storageAddress'])
                except Exception as e:
                    return e
                else:
                    if computed_hash == pkhash:
                        # save challenge in local db for later use
                        instance = Algo.objects.create(pkhash=pkhash,
                                                       description=algo['description']['storageAddress'],
                                                       file=algo['storageAddress'],
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
            'args': '{"Args":["queryAlgos"]}'
        })
        challengeData = None
        datasetData = None
        modelData = None

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
                        if k == 'algo':  # filter by own key
                            for key, val in subfilters.items():
                                l[idx] = [x for x in l[idx] if x[key] in val]
                        elif k == 'challenge':  # select challenge used by these datasets
                            st = None
                            if not challengeData:
                                # TODO find a way to put this call in cache
                                challengeData, st = queryLedger({
                                    'org': org,
                                    'peer': peer,
                                    'args': '{"Args":["queryChallenges"]}'
                                })

                                if st != 200:
                                    return Response(challengeData, status=st)

                            for key, val in subfilters.items():
                                if key == 'metrics':  # specific to nested metrics
                                    filteredData = [x for x in challengeData if x[key]['name'] in val]
                                else:
                                    filteredData = [x for x in challengeData if x[key] in val]
                                challengeKeys = [x['key'] for x in filteredData]
                                l[idx] = [x for x in l[idx] if x['challengeKey'] in challengeKeys]
                        elif k == 'dataset':  # select challenge used by these algo
                            if not datasetData:
                                # TODO find a way to put this call in cache
                                datasetData, st = queryLedger({
                                    'org': org,
                                    'peer': peer,
                                    'args': '{"Args":["queryDatasets"]}'
                                })
                                if st != 200:
                                    return Response(datasetData, status=st)

                            for key, val in subfilters.items():
                                filteredData = [x for x in datasetData if x[key] in val]
                                challengeKeys = list(itertools.chain.from_iterable([x['challengeKeys'] for x in filteredData]))
                                l[idx] = [x for x in l[idx] if x['challengeKey'] in challengeKeys]
                        elif k == 'model':  # select challenges used by endModel hash
                            if not modelData:
                                # TODO find a way to put this call in cache
                                modelData, st = queryLedger({
                                    'org': org,
                                    'peer': peer,
                                    'args': '{"Args":["queryModels"]}'
                                })
                                if st != 200:
                                    return Response(modelData, status=st)

                            for key, val in subfilters.items():
                                filteredData = [x for x in modelData if x['endModel'][key] in val]
                                challengeKeys = [x['challenge']['hash'] for x in filteredData]
                                l[idx] = [x for x in l[idx] if x['challengeKey'] in challengeKeys]

        return Response(l, status=st)

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

import hashlib

import requests
from django.db import IntegrityError
from django.http import Http404
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
from substrapp.views.utils import get_filters


class DatasetViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     GenericViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer

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
                dataset, st = queryLedger({
                    'org': org,
                    'peer': peer,
                    'args': '{"Args":["queryDatasetData","%s"]}' % pk
                })

                # check dataopener hash
                try:
                    r = requests.get(dataset[pk]['openerStorageAddress'])
                except:
                    return Response({'message': 'Failed to check hash due to failed opener fetch file %s' %
                                                dataset[pk]['openerStorageAddress']}, status.HTTP_400_BAD_REQUEST)
                else:
                    if r.status_code == 200:
                        opener_file = r.content

                        sha256_hash = hashlib.sha256()
                        if isinstance(opener_file, str):
                            description_file = opener_file.encode()
                        sha256_hash.update(opener_file)
                        computedHash = sha256_hash.hexdigest()

                        if computedHash == pkhash:
                            # check description hash
                            try:
                                r = requests.get(dataset[pk]['description']['storageAddress'])
                            except:
                                return Response(
                                    {'message': 'Failed to check hash due to failed description fetch file %s' %
                                                dataset[pk]['description']['storageAddress']},
                                    status.HTTP_400_BAD_REQUEST)
                            else:
                                if r.status_code == 200:
                                    description_file = r.content

                                    sha256_hash = hashlib.sha256()
                                    if isinstance(description_file, str):
                                        description_file = description_file.encode()
                                    sha256_hash.update(description_file)
                                    computedHash = sha256_hash.hexdigest()

                                    if computedHash == dataset[pk]['description']['hash']:
                                        # save dataset in local db for later use
                                        instance = Dataset.objects.create(pkhash=pkhash,
                                                                          name=dataset[pk]['name'],
                                                                          description=dataset[pk]['description'][
                                                                              'storageAddress'],
                                                                          data_opener=dataset[pk][
                                                                              'openerStorageAddress'],
                                                                          validated=True)

                        return Response({
                            'message': 'computedHash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'},
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
            'args': '{"Args":["queryDatasets"]}'
        })
        challengeData = None
        algoData = None
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
                        if k == 'dataset':  # filter by own key
                            for key, val in subfilters.items():
                                l[idx] = [x for x in l[idx] if x[key] in val]
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
                                l[idx] = [x for x in l[idx] if [x for x in x['challengeKeys'] if x in challengeKeys]]
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
                                l[idx] = [x for x in l[idx] if [x for x in x['challengeKeys'] if x in challengeKeys]]
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
                                l[idx] = [x for x in l[idx] if [x for x in x['challengeKeys'] if x in challengeKeys]]

        return Response(l, status=st)

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
                                                              'challenge_keys': data.getlist('challenge_keys'),
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

    # TODO create data list related to model

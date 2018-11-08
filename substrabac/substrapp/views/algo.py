import itertools
import tempfile

import requests
from django.conf import settings
from django.db import IntegrityError
from django.http import Http404
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.models import Algo, Challenge
from substrapp.serializers import LedgerAlgoSerializer, AlgoSerializer
from substrapp.utils import queryLedger
from substrapp.views.utils import get_filters, getObjectFromLedger, ComputeHashMixin, ManageFileMixin, JsonException


class AlgoViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  ComputeHashMixin,
                  ManageFileMixin,
                  GenericViewSet):
    queryset = Algo.objects.all()
    serializer_class = AlgoSerializer

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = request.data

        serializer = self.get_serializer(data={'file': data.get('file'), 'description': data.get('description')})
        serializer.is_valid(raise_exception=True)

        # create on db
        try:
            instance = self.perform_create(serializer)
        except IntegrityError as exc:
            return Response({
                'message': 'An Algo with these data values already exists.'},
                status=status.HTTP_409_CONFLICT)
        except Exception as exc:
            return Response({'message': exc.args},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            # init ledger serializer
            ledger_serializer = LedgerAlgoSerializer(data={'name': data.get('name'),
                                                           'permissions': data.get('permissions', 'all'),
                                                           'challenge_key': data.get('challenge_key'),
                                                           'instance': instance},
                                                     context={'request': request})
            if not ledger_serializer.is_valid():
                # delete instance
                instance.delete()
                raise ValidationError(ledger_serializer.errors)

            # create on ledger
            data, st = ledger_serializer.create(ledger_serializer.validated_data)

            headers = self.get_success_headers(serializer.data)

            d = dict(serializer.data)
            d.update(data)
            return Response(d, status=st, headers=headers)

    def create_or_update_algo(self, algo, pk):
        try:
            # get challenge description from remote node
            url = algo['description']['storageAddress']
            try:
                r = requests.get(url, headers={'Accept': 'application/json;version=0.0'})  # TODO pass cert
            except:
                raise Exception('Failed to fetch %s' % url)
            else:
                if r.status_code != 200:
                    raise Exception('end to end node report %s' % r.text)

                try:
                    computed_hash = self.compute_hash(r.content)
                except Exception:
                    raise Exception('Failed to fetch description file')
                else:
                    if computed_hash != algo['description']['hash']:
                        msg = 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'
                        raise Exception(msg)

                    f = tempfile.TemporaryFile()
                    f.write(r.content)

                    # save/update challenge in local db for later use
                    instance, created = Algo.objects.update_or_create(pkhash=pk, validated=True)
                    instance.description.save('description.md', f)
        except Exception as e:
            raise e
        else:
            return instance

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        if len(pk) != 64:
            return Response({'message': 'Wrong pk %s' % pk}, status.HTTP_400_BAD_REQUEST)

        try:
            int(pk, 16)  # test if pk is correct (hexadecimal)
        except:
            return Response({'message': 'Wrong pk %s' % pk}, status.HTTP_400_BAD_REQUEST)
        else:
            # get instance from remote node
            error = None
            instance = None
            try:
                data = getObjectFromLedger(pk)
            except JsonException as e:
                return Response(e.msg, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    # try to get it from local db to check if description exists
                    instance = self.get_object()
                except Http404:
                    try:
                        instance = self.create_or_update_algo(data, pk)
                    except Exception as e:
                        error = e
                else:
                    # check if instance has description
                    if not instance.description:
                        try:
                            instance = self.create_or_update_algo(data, pk)
                        except Exception as e:
                            error = e
                finally:
                    if error is not None:
                        return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

                    # do not give access to local files address
                    if instance is not None:
                        serializer = self.get_serializer(instance, fields=('owner', 'pkhash', 'creation_date', 'last_modified'))
                        data.update(serializer.data)
                    else:
                        data = {'message': 'Fail to get instance'}

                    return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        # can modify result by interrogating `request.version`

        data, st = queryLedger({
            'org': settings.LEDGER['org'],
            'peer': settings.LEDGER['peer'],
            'args': '{"Args":["queryAlgos"]}'
        })
        challengeData = None
        datasetData = None
        modelData = None

        # init list to return
        if data is None:
            data = []
        l = [data]

        if st == 200:

            # parse filters
            query_params = request.query_params.get('search', None)

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
                                        'org': settings.LEDGER['org'],
                                        'peer': settings.LEDGER['peer'],
                                        'args': '{"Args":["queryChallenges"]}'
                                    })

                                    if st != 200:
                                        return Response(challengeData, status=st)
                                    if challengeData is None:
                                        challengeData = []

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
                                        'org': settings.LEDGER['org'],
                                        'peer': settings.LEDGER['peer'],
                                        'args': '{"Args":["queryDatasets"]}'
                                    })
                                    if st != 200:
                                        return Response(datasetData, status=st)
                                    if datasetData is None:
                                        datasetData = []

                                for key, val in subfilters.items():
                                    filteredData = [x for x in datasetData if x[key] in val]
                                    challengeKeys = list(
                                        itertools.chain.from_iterable([x['challengeKeys'] for x in filteredData]))
                                    l[idx] = [x for x in l[idx] if x['challengeKey'] in challengeKeys]
                            elif k == 'model':  # select challenges used by endModel hash
                                if not modelData:
                                    # TODO find a way to put this call in cache
                                    modelData, st = queryLedger({
                                        'org': settings.LEDGER['org'],
                                        'peer': settings.LEDGER['peer'],
                                        'args': '{"Args":["queryTraintuples"]}'
                                    })
                                    if st != 200:
                                        return Response(modelData, status=st)
                                    if modelData is None:
                                        modelData = []

                                for key, val in subfilters.items():
                                    filteredData = [x for x in modelData if x['endModel'][key] in val]
                                    challengeKeys = [x['challenge']['hash'] for x in filteredData]
                                    l[idx] = [x for x in l[idx] if x['challengeKey'] in challengeKeys]

        return Response(l, status=st)

    @action(detail=True)
    def file(self, request, *args, **kwargs):
        return self.manage_file('file')

    @action(detail=True)
    def description(self, request, *args, **kwargs):
        return self.manage_file('description')
